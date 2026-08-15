from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from . import selectors, services
from .forms import PollForm

POLLS_PER_PAGE = 20

TABS = {"yeni", "populer", "kapananlar"}


def index(request):
    tab = request.GET.get("sekme", "yeni")
    if tab not in TABS:
        tab = "yeni"

    if tab == "populer":
        polls = selectors.list_popular_polls()
    elif tab == "kapananlar":
        polls = selectors.list_closed_polls()
    else:
        polls = selectors.list_new_polls()

    paginator = Paginator(polls, POLLS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "polls/index.html", {"page_obj": page_obj, "active_tab": tab})


def detail(request, public_id):
    poll = get_object_or_404(selectors.get_poll_detail_queryset(), public_id=public_id)
    return render(request, "polls/detail.html", {"poll": poll})


@login_required
def create(request):
    if request.method == "POST":
        form = PollForm(request.POST, user=request.user)
        if form.is_valid():
            poll = services.create_poll(
                user=request.user,
                question=form.cleaned_data["question"],
                description=form.cleaned_data["description"],
                options=form.options,
            )
            messages.success(request, "Anketin yayında.")
            return redirect(poll.get_absolute_url())
    else:
        form = PollForm(user=request.user)

    return render(request, "polls/create.html", {"form": form})


def profile(request, username):
    profile_user = get_object_or_404(get_user_model(), username__iexact=username)
    polls = selectors.list_user_polls(profile_user)
    return render(request, "polls/profile.html", {"profile_user": profile_user, "polls": polls})
