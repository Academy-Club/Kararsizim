from unittest import mock

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from . import selectors, services
from .models import Option, Poll, Vote

User = get_user_model()


def create_user(username="yazar", email="yazar@example.com"):
    return User.objects.create_user(username=username, email=email, password="guclu-parola-123")


class PollCreateViewTests(TestCase):
    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("polls:create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_single_option_rejected(self):
        user = create_user()
        self.client.force_login(user)
        response = self.client.post(reverse("polls:create"), {
            "question": "Bugün ne yapsam acaba?",
            "description": "",
            "option": ["Tek seçenek"],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Poll.objects.count(), 0)

    def test_six_options_rejected(self):
        user = create_user()
        self.client.force_login(user)
        response = self.client.post(reverse("polls:create"), {
            "question": "Bugün ne yapsam acaba?",
            "description": "",
            "option": ["Bir", "İki", "Üç", "Dört", "Beş", "Altı"],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Poll.objects.count(), 0)

    def test_duplicate_option_text_rejected(self):
        user = create_user()
        self.client.force_login(user)
        response = self.client.post(reverse("polls:create"), {
            "question": "Bugün ne yapsam acaba?",
            "description": "",
            "option": ["Sinema", "sinema"],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Poll.objects.count(), 0)

    def test_valid_submission_creates_poll(self):
        user = create_user()
        self.client.force_login(user)
        response = self.client.post(reverse("polls:create"), {
            "question": "Bugün ne yapsam acaba?",
            "description": "",
            "option": ["Sinema", "Tiyatro"],
        })
        poll = Poll.objects.get()
        self.assertRedirects(response, poll.get_absolute_url())
        self.assertEqual(poll.options.count(), 2)

    def test_daily_limit_enforced(self):
        user = create_user()
        for i in range(10):
            Poll.objects.create(author=user, question=f"Soru numarası {i} nedir acaba?")
        self.client.force_login(user)
        response = self.client.post(reverse("polls:create"), {
            "question": "On birinci anket olabilir mi acaba?",
            "description": "",
            "option": ["Evet", "Hayır"],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Poll.objects.count(), 10)


class IndexViewQueryCountTests(TestCase):
    def _create_polls(self, user, count):
        for i in range(count):
            poll = Poll.objects.create(
                author=user, question=f"Soru numarası {i} nedir acaba?", total_votes=5
            )
            Option.objects.create(poll=poll, text="A", position=0, vote_count=3)
            Option.objects.create(poll=poll, text="B", position=1, vote_count=2)

    def test_query_count_does_not_grow_with_poll_count(self):
        user = create_user()
        self._create_polls(user, 3)

        with CaptureQueriesContext(connection) as small_context:
            response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)

        Poll.objects.all().delete()
        self._create_polls(user, 25)

        with CaptureQueriesContext(connection) as large_context:
            response = self.client.get(reverse("polls:index"))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(small_context.captured_queries), len(large_context.captured_queries))


class PollVoteTests(TestCase):
    def setUp(self):
        self.author = create_user(username="anketsahibi", email="sahibi@example.com")
        self.poll = Poll.objects.create(author=self.author, question="Bugün ne yapsak acaba?")
        self.option_a = Option.objects.create(poll=self.poll, text="A", position=0)
        self.option_b = Option.objects.create(poll=self.poll, text="B", position=1)

    def test_anonymous_vote_succeeds_and_increments_counts(self):
        response = self.client.post(
            reverse("polls:vote", args=[self.poll.public_id]),
            {"option_id": self.option_a.id},
        )
        self.assertRedirects(response, self.poll.get_absolute_url())
        self.option_a.refresh_from_db()
        self.poll.refresh_from_db()
        self.assertEqual(self.option_a.vote_count, 1)
        self.assertEqual(self.poll.total_votes, 1)

    def test_same_session_second_vote_returns_409(self):
        url = reverse("polls:vote", args=[self.poll.public_id])
        self.client.post(url, {"option_id": self.option_a.id})
        response = self.client.post(
            url, {"option_id": self.option_b.id}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 409)
        self.poll.refresh_from_db()
        self.assertEqual(self.poll.total_votes, 1)

    def test_same_user_second_vote_returns_409(self):
        voter = create_user(username="oyveren", email="oyveren@example.com")
        self.client.force_login(voter)
        url = reverse("polls:vote", args=[self.poll.public_id])
        self.client.post(url, {"option_id": self.option_a.id})
        response = self.client.post(
            url, {"option_id": self.option_b.id}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 409)
        self.poll.refresh_from_db()
        self.assertEqual(self.poll.total_votes, 1)

    def test_option_from_another_poll_returns_400(self):
        other_poll = Poll.objects.create(author=self.author, question="Başka bir soru mu bu?")
        other_option = Option.objects.create(poll=other_poll, text="X", position=0)
        response = self.client.post(
            reverse("polls:vote", args=[self.poll.public_id]),
            {"option_id": other_option.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)

    def test_closed_poll_vote_returns_403(self):
        self.poll.status = Poll.STATUS_CLOSED
        self.poll.save(update_fields=["status"])
        response = self.client.post(
            reverse("polls:vote", args=[self.poll.public_id]),
            {"option_id": self.option_a.id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 403)

    def test_owner_sees_vote_form_and_can_vote_on_own_poll(self):
        """Regresyon: anket sahibi henüz oy vermemişse sonuçları görebilmeli
        AMA oy verme formu da gösterilmeli (yazar kendi anketine oy verebilir)."""
        self.client.force_login(self.author)
        detail_response = self.client.get(reverse("polls:detail", args=[self.poll.public_id]))
        self.assertContains(detail_response, "option-vote-form")
        self.assertContains(detail_response, "%")  # sahip yüzdeleri de görebilmeli

        vote_response = self.client.post(
            reverse("polls:vote", args=[self.poll.public_id]), {"option_id": self.option_a.id}
        )
        self.assertRedirects(vote_response, self.poll.get_absolute_url())
        self.option_a.refresh_from_db()
        self.assertEqual(self.option_a.vote_count, 1)

    def test_race_condition_falls_back_to_integrity_error(self):
        """Pre-check'i atlatan eşzamanlı bir isteği simüle eder: DB constraint'i
        yine de AlreadyVotedError'a çevrilmeli, ikinci sayaç artışı olmamalı."""
        Vote.objects.create(poll=self.poll, option=self.option_a, user=None, voter_key="race-key")
        with mock.patch("polls.services.selectors.get_voted_option_id", return_value=None):
            with self.assertRaises(services.AlreadyVotedError):
                services.cast_vote(
                    poll=self.poll, option_id=self.option_a.id, user=None, voter_key="race-key"
                )
        self.option_a.refresh_from_db()
        self.assertEqual(self.option_a.vote_count, 0)


class PollPercentageRoundingTests(TestCase):
    def _poll_with_votes(self, counts):
        author = create_user(username=f"yuvarlama{len(counts)}", email=f"y{len(counts)}@example.com")
        poll = Poll.objects.create(author=author, question="Bu seçenekler arasında ne olsun?")
        total = 0
        for position, count in enumerate(counts):
            Option.objects.create(poll=poll, text=str(position), position=position, vote_count=count)
            total += count
        poll.total_votes = total
        poll.save(update_fields=["total_votes"])
        return poll

    def test_percentages_sum_to_100_with_three_way_split(self):
        poll = self._poll_with_votes([1, 1, 1])
        payload = selectors.build_poll_results(poll, user=None, voter_key="test")
        self.assertEqual(sum(option["percent"] for option in payload["options"]), 100)

    def test_percentages_sum_to_100_with_seven_votes(self):
        poll = self._poll_with_votes([3, 2, 2])
        payload = selectors.build_poll_results(poll, user=None, voter_key="test")
        self.assertEqual(sum(option["percent"] for option in payload["options"]), 100)


class PollCloseDeleteTests(TestCase):
    def setUp(self):
        self.author = create_user(username="sahip", email="sahip@example.com")
        self.other_user = create_user(username="baskasi", email="baskasi@example.com")
        self.poll = Poll.objects.create(author=self.author, question="Kapatılacak anket mi bu?")
        Option.objects.create(poll=self.poll, text="A", position=0)
        Option.objects.create(poll=self.poll, text="B", position=1)

    def test_non_owner_cannot_close(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse("polls:close", args=[self.poll.public_id]))
        self.assertEqual(response.status_code, 403)

    def test_owner_can_close(self):
        self.client.force_login(self.author)
        response = self.client.post(reverse("polls:close", args=[self.poll.public_id]))
        self.assertRedirects(response, self.poll.get_absolute_url())
        self.poll.refresh_from_db()
        self.assertEqual(self.poll.status, Poll.STATUS_CLOSED)

    def test_delete_requires_confirmation_get_then_post(self):
        self.client.force_login(self.author)
        url = reverse("polls:delete", args=[self.poll.public_id])
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(Poll.objects.count(), 1)

        post_response = self.client.post(url)
        self.assertRedirects(post_response, reverse("polls:index"))
        self.assertEqual(Poll.objects.count(), 0)

    def test_non_owner_cannot_delete(self):
        self.client.force_login(self.other_user)
        response = self.client.post(reverse("polls:delete", args=[self.poll.public_id]))
        self.assertEqual(response.status_code, 403)
