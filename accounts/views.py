from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import LoginForm, RegisterForm

CREATE_POLL_PATH = "/anket/olustur/"


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


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_create_poll_notice"] = self.get_redirect_url() == CREATE_POLL_PATH
        return context
