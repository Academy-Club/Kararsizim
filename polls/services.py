from django.db import transaction

from .models import Option, Poll


@transaction.atomic
def create_poll(*, user, question, description, options):
    poll = Poll.objects.create(author=user, question=question, description=description)
    Option.objects.bulk_create(
        Option(poll=poll, text=text, position=position)
        for position, text in enumerate(options)
    )
    return poll
