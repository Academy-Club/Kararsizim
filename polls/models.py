from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from .utils import generate_public_id


class Poll(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Aktif"),
        (STATUS_CLOSED, "Kapalı"),
    ]

    public_id = models.CharField(max_length=12, unique=True, db_index=True, blank=True)
    question = models.CharField(max_length=140, validators=[MinLengthValidator(10)])
    description = models.CharField(max_length=280, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="polls"
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    total_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    closes_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.question

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = self._generate_unique_public_id()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_unique_public_id():
        for _ in range(10):
            candidate = generate_public_id()
            if not Poll.objects.filter(public_id=candidate).exists():
                return candidate
        raise RuntimeError("public_id üretilemedi")

    @property
    def is_open(self):
        if self.status != self.STATUS_ACTIVE:
            return False
        return self.closes_at is None or self.closes_at > timezone.now()

    def get_absolute_url(self):
        return f"/anket/{self.public_id}/"

    @property
    def indecision_badge(self):
        if self.total_votes == 0:
            return "İlk oyu sen ver"
        options = list(self.options.all())
        if len(options) < 2:
            return "Karar net"
        top_two = sorted(options, key=lambda option: option.vote_count, reverse=True)[:2]
        diff_percent = abs(top_two[0].vote_count - top_two[1].vote_count) / self.total_votes * 100
        if diff_percent <= 5:
            return "Kalabalık da kararsız"
        if diff_percent <= 20:
            return "Az farkla önde"
        return "Karar net"


class Option(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=80)
    position = models.PositiveSmallIntegerField()
    vote_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(fields=["poll", "position"], name="uniq_option_position"),
        ]

    def __str__(self):
        return self.text


class Vote(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="votes")
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="votes",
    )
    voter_key = models.CharField(max_length=64, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["poll", "user"],
                condition=Q(user__isnull=False),
                name="uniq_vote_per_user",
            ),
            models.UniqueConstraint(
                fields=["poll", "voter_key"],
                condition=Q(user__isnull=True),
                name="uniq_vote_per_anon",
            ),
        ]

    def __str__(self):
        return f"{self.poll_id} → {self.option_id}"
