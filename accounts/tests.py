from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import RegisterForm

User = get_user_model()


def valid_register_data(**overrides):
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password1": "guclu-parola-123",
        "password2": "guclu-parola-123",
    }
    data.update(overrides)
    return data


class RegisterFormTests(TestCase):
    def test_duplicate_email_rejected(self):
        User.objects.create_user(
            username="ilkkullanici", email="ayni@example.com", password="guclu-parola-123"
        )
        form = RegisterForm(
            data=valid_register_data(username="ikincikullanici", email="AYNI@example.com")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_case_insensitive_username_taken(self):
        User.objects.create_user(
            username="KullaniciAdi", email="a@example.com", password="guclu-parola-123"
        )
        form = RegisterForm(data=valid_register_data(username="kullaniciadi", email="b@example.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_invalid_username_characters_rejected(self):
        form = RegisterForm(data=valid_register_data(username="gecersiz ad!"))
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)


class AuthFlowTests(TestCase):
    def test_register_login_logout_flow_and_no_email_leak(self):
        response = self.client.post(reverse("accounts:register"), valid_register_data(
            username="akingunes", email="akin@example.com"
        ))
        self.assertRedirects(response, reverse("polls:index"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

        self.client.logout()

        response = self.client.post(reverse("accounts:login"), {
            "username": "akingunes",
            "password": "guclu-parola-123",
        })
        self.assertRedirects(response, "/")

        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "@akingunes")
        self.assertNotContains(response, "akin@example.com")

        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, "/")
