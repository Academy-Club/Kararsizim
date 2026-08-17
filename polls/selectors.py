from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from .models import Poll, Vote

RECENT_VOTES_WINDOW = timedelta(days=7)


def _base_queryset():
    return Poll.objects.select_related("author").prefetch_related("options")


def list_new_polls():
    return _base_queryset().order_by("-created_at")


def list_popular_polls():
    cutoff = timezone.now() - RECENT_VOTES_WINDOW
    return (
        _base_queryset()
        .annotate(recent_votes=Count("votes", filter=Q(votes__created_at__gte=cutoff)))
        .order_by("-recent_votes", "-total_votes", "-created_at")
    )


def list_closed_polls():
    return _base_queryset().filter(status=Poll.STATUS_CLOSED).order_by("-created_at")


def get_poll_detail_queryset():
    return _base_queryset()


def list_user_polls(user):
    return _base_queryset().filter(author=user).order_by("-created_at")


def count_polls_created_today(user):
    return Poll.objects.filter(author=user, created_at__date=timezone.localdate()).count()


def get_voted_option_id(poll, *, user, voter_key):
    if user is not None and user.is_authenticated:
        vote = Vote.objects.filter(poll=poll, user=user).only("option_id").first()
    else:
        vote = (
            Vote.objects.filter(poll=poll, voter_key=voter_key, user__isnull=True)
            .only("option_id")
            .first()
        )
    return vote.option_id if vote else None


def compute_percentages(options):
    total = sum(option.vote_count for option in options)
    if total == 0:
        return {option.id: 0 for option in options}
    percentages = {option.id: round(option.vote_count / total * 100) for option in options}
    diff = 100 - sum(percentages.values())
    if diff:
        largest = max(options, key=lambda option: option.vote_count)
        percentages[largest.id] += diff
    return percentages


def build_poll_results(poll, *, user, voter_key, is_owner=False):
    voted_option_id = get_voted_option_id(poll, user=user, voter_key=voter_key)
    reveal_results = not poll.is_open or voted_option_id is not None or is_owner

    options = list(poll.options.all())
    percentages = compute_percentages(options) if reveal_results else None
    return {
        "total": poll.total_votes,
        "options": [
            {
                "id": option.id,
                "text": option.text,
                "count": option.vote_count if reveal_results else None,
                "percent": percentages[option.id] if reveal_results else None,
            }
            for option in options
        ],
        "voted_option_id": voted_option_id,
        "is_open": poll.is_open,
        "reveal_results": reveal_results,
    }
