from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import Option, Poll

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
