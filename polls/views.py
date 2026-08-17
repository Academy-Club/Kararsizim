from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from . import selectors, services
from .forms import PollForm
from .models import Poll
from .utils import get_voter_key

POLLS_PER_PAGE = 20

TABS = {"yeni", "populer", "kapananlar"}


def _wants_json(request):
    return (
        request.headers.get("Accept") == "application/json"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


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
    user = request.user if request.user.is_authenticated else None
    voter_key = get_voter_key(request)
    voted_option_id = selectors.get_voted_option_id(poll, user=user, voter_key=voter_key)
    is_owner = user is not None and poll.author_id == user.id

    # can_vote ve reveal_results birbirinden bağımsızdır: anket sahibi henüz
    # oy vermemişken bile sonuçları görebilir (Bölüm 6), ama bu onun oy
    # verme hakkını (Bölüm 6: "yazar kendi anketine oy verebilir") elinden
    # almamalı — bu yüzden iki bayrak aynı anda true olabilir.
    can_vote = poll.is_open and voted_option_id is None
    reveal_results = not poll.is_open or voted_option_id is not None or is_owner

    if reveal_results:
        percentages = selectors.compute_percentages(list(poll.options.all()))
        for option in poll.options.all():
            option.percent = percentages[option.id]

    context = {
        "poll": poll,
        "voted_option_id": voted_option_id,
        "can_vote": can_vote,
        "reveal_results": reveal_results,
    }
    return render(request, "polls/detail.html", context)


@require_POST
def vote(request, public_id):
    poll = get_object_or_404(selectors.get_poll_detail_queryset(), public_id=public_id)
    user = request.user if request.user.is_authenticated else None
    voter_key = get_voter_key(request)
    is_owner = user is not None and poll.author_id == user.id

    error_message = None
    status_code = 200
    try:
        services.cast_vote(
            poll=poll, option_id=request.POST.get("option_id"), user=user, voter_key=voter_key
        )
    except services.PollClosedError:
        status_code = 403
        error_message = "Bu anket kapalı, oy kullanılamıyor."
    except services.InvalidOptionError:
        status_code = 400
        error_message = "Geçersiz seçenek."
    except services.AlreadyVotedError:
        status_code = 409
        error_message = "Bu ankete zaten oy verdin."

    poll.refresh_from_db()

    if error_message is None:
        voted_polls = request.session.get("voted_polls", [])
        if poll.public_id not in voted_polls:
            voted_polls.append(poll.public_id)
            request.session["voted_polls"] = voted_polls

    if _wants_json(request):
        payload = selectors.build_poll_results(
            poll, user=user, voter_key=voter_key, is_owner=is_owner
        )
        if error_message:
            payload["error"] = error_message
        return JsonResponse(payload, status=status_code)

    if error_message:
        messages.error(request, error_message)
    return redirect(poll.get_absolute_url())


@require_GET
def results(request, public_id):
    poll = get_object_or_404(selectors.get_poll_detail_queryset(), public_id=public_id)
    user = request.user if request.user.is_authenticated else None
    voter_key = get_voter_key(request)
    is_owner = user is not None and poll.author_id == user.id
    return JsonResponse(
        selectors.build_poll_results(poll, user=user, voter_key=voter_key, is_owner=is_owner)
    )


@login_required
@require_POST
def close(request, public_id):
    poll = get_object_or_404(Poll, public_id=public_id)
    if poll.author_id != request.user.id:
        raise PermissionDenied
    services.close_poll(poll)
    messages.success(request, "Anket kapatıldı.")
    return redirect(poll.get_absolute_url())


@login_required
def delete(request, public_id):
    poll = get_object_or_404(Poll, public_id=public_id)
    if poll.author_id != request.user.id:
        raise PermissionDenied

    if request.method == "POST":
        poll.delete()
        messages.success(request, "Anket silindi.")
        return redirect("polls:index")

    return render(request, "polls/delete_confirm.html", {"poll": poll})


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
