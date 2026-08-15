from django.db import IntegrityError, transaction
from django.db.models import F

from . import selectors
from .models import Option, Poll, Vote


class PollClosedError(Exception):
    """Anket kapalı, oy kabul edilmiyor."""


class InvalidOptionError(Exception):
    """Seçenek bu ankete ait değil."""


class AlreadyVotedError(Exception):
    """Bu kişi zaten oy kullanmış."""


@transaction.atomic
def create_poll(*, user, question, description, options):
    poll = Poll.objects.create(author=user, question=question, description=description)
    Option.objects.bulk_create(
        Option(poll=poll, text=text, position=position)
        for position, text in enumerate(options)
    )
    return poll


@transaction.atomic
def cast_vote(*, poll, option_id, user, voter_key):
    if not poll.is_open:
        raise PollClosedError

    try:
        option = Option.objects.get(pk=option_id, poll_id=poll.pk)
    except (Option.DoesNotExist, ValueError, TypeError):
        raise InvalidOptionError

    vote_user = user if user is not None and user.is_authenticated else None

    if selectors.get_voted_option_id(poll, user=vote_user, voter_key=voter_key) is not None:
        raise AlreadyVotedError

    try:
        Vote.objects.create(poll=poll, option=option, user=vote_user, voter_key=voter_key)
    except IntegrityError:
        raise AlreadyVotedError

    Option.objects.filter(pk=option.pk).update(vote_count=F("vote_count") + 1)
    Poll.objects.filter(pk=poll.pk).update(total_votes=F("total_votes") + 1)


def close_poll(poll):
    Poll.objects.filter(pk=poll.pk).update(status=Poll.STATUS_CLOSED)
