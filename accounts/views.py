from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from .forms import LoginForm, RegisterForm


def register(request):
    if request.user.is_authenticated:
        return redirect("polls:index")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, f"Hoş geldin, @{user.username}")
            return redirect("polls:index")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


# Tek IP'nin çok sayıda hesabı denemesine (kaba kuvvet) ve tek bir hesabın
# çok sayıda IP'den hedef alınmasına (dağıtık deneme) karşı iki ayrı limit.
@method_decorator(ratelimit(key="ip", rate="20/5m", method="POST"), name="post")
@method_decorator(ratelimit(key="post:username", rate="5/5m", method="POST"), name="post")
class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_create_poll_notice"] = self.get_redirect_url() == reverse("polls:create")
        return context
