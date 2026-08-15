from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import USERNAME_REGEX_VALIDATOR, validate_username_not_forbidden

User = get_user_model()


class RegisterForm(forms.Form):
    username = forms.CharField(
        label="Kullanıcı adı",
        max_length=20,
        validators=[USERNAME_REGEX_VALIDATOR, validate_username_not_forbidden],
    )
    email = forms.EmailField(label="E-posta")
    password1 = forms.CharField(label="Parola", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Parola (tekrar)", widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Bu kullanıcı adı zaten alınmış.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Bu e-posta adresiyle zaten bir hesap var.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Parolalar birbiriyle uyuşmuyor.")
        return password2

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        if password1:
            try:
                validate_password(password1)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned_data

    def save(self):
        user = User(username=self.cleaned_data["username"], email=self.cleaned_data["email"])
        user.set_password(self.cleaned_data["password1"])
        user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Kullanıcı adı")
    password = forms.CharField(label="Parola", widget=forms.PasswordInput)
