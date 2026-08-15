from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from .models import Poll

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
