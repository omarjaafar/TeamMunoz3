from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .forms import ProfilePrivacyForm, ProfileEditForm
from .utils import pretty_filters_from_querystring

from .models import Profile
from .models import Profile, CandidateSavedSearch, CandidateSearchNotification, apply_candidate_querystring_filters
from .forms import CandidateSavedSearchForm


def signup(request):
    template_data = {'title': 'Sign Up'}
    if request.method == 'GET':
        template_data['form'] = UserCreationForm()
        return render(request, 'accounts/signup.html', {'template_data': template_data})

    elif request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = request.POST.get('role', Profile.JOB_SEEKER)
            if role == 'ADMIN':
                user.is_staff = True
                user.is_superuser = True
                user.save()
            Profile.objects.create(user=user, role=role)
            auth_login(request, user)
            return redirect('home.index')
        else:
            template_data['form'] = form
            return render(request, 'accounts/signup.html', {'template_data': template_data})


@login_required
def logout(request):
    auth_logout(request)
    return redirect('home.index')


def login(request):
    template_data = {'title': 'Login'}
    if request.method == 'GET':
        return render(request, 'accounts/login.html', {'template_data': template_data})
    elif request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/login.html', {'template_data': template_data})
        else:
            auth_login(request, user)
            return redirect('home.index')


@login_required
def edit_privacy(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfilePrivacyForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Privacy settings updated.")
            return redirect('accounts.edit_privacy')
    else:
        form = ProfilePrivacyForm(instance=profile)
    return render(request, 'accounts/privacy_settings.html', {'form': form})


@login_required
def seeker_settings(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile information updated successfully.")
            return redirect('seeker.settings')
    else:
        form = ProfileEditForm(instance=profile)

    template_data = {
        'title': 'Settings',
        'form': form,
    }
    return render(request, 'home/seeker_settings.html', {'template_data': template_data})

@login_required
def edit_profile(request):
    profile = request.user.profile
    form = ProfileEditForm(request.POST or None, instance=profile)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profile information updated successfully.")
        return redirect('seeker.settings')

    return render(request, 'accounts/edit_profile.html', {'form': form})

def _require_recruiter(request):
    profile = getattr(request.user, "profile", None)
    return bool(profile and profile.role == "RECRUITER")

@login_required
def candidate_search(request):
    if not _require_recruiter(request):
        messages.error(request, "Only recruiters can access candidate search.")
        return redirect("home:index")

    qs = Profile.objects.select_related("user").all()
    qs = apply_candidate_querystring_filters(qs, request.META.get("QUERY_STRING", ""))

    return render(request, "accounts/candidate_search.html", {
        "profiles": qs,
    })

@login_required
@require_http_methods(["GET", "POST"])
def candidate_saved_search_create(request):
    if not _require_recruiter(request):
        messages.error(request, "Only recruiters can save searches.")
        return redirect("home:index")

    if request.method == "POST":
        form = CandidateSavedSearchForm(request.POST)
        if form.is_valid():
            ss = form.save(commit=False)
            ss.recruiter = request.user
            ss.querystring = request.META.get("QUERY_STRING", "")
            ss.save()
            messages.success(request, "Candidate search saved.")
            return redirect("accounts.candidate_saved_search_list")
    else:
        default_name = (request.GET.get("skills") or request.GET.get("q") or "My candidate search")
        form = CandidateSavedSearchForm(initial={"name": default_name})

    return render(request, "accounts/candidate_saved_search_create.html", {"form": form})

@login_required
def candidate_saved_search_list(request):
    if not _require_recruiter(request):
        messages.error(request, "Only recruiters can view saved searches.")
        return redirect("home.index")  # keep your dotted name style

    searches = CandidateSavedSearch.objects.filter(recruiter=request.user)

    # Attach pretty filters for display
    for s in searches:
        s.pretty_filters = pretty_filters_from_querystring(s.querystring)

    return render(
        request,
        "accounts/candidate_saved_search_list.html",
        {"searches": searches},
    )

@login_required
@require_http_methods(["POST"])
def candidate_saved_search_delete(request, pk):
    ss = get_object_or_404(CandidateSavedSearch, pk=pk, recruiter=request.user)
    ss.delete()
    messages.success(request, "Saved search deleted.")
    return redirect("accounts.candidate_saved_search_list")

@login_required
@require_http_methods(["POST"])
def candidate_saved_search_toggle_email(request, pk):
    ss = get_object_or_404(CandidateSavedSearch, pk=pk, recruiter=request.user)
    ss.email_enabled = not ss.email_enabled
    ss.save(update_fields=["email_enabled"])
    messages.success(request, f"Email notifications {'enabled' if ss.email_enabled else 'disabled'}.")
    return redirect("accounts:candidate_saved_search_list")

@login_required
def candidate_saved_search_notifications(request, pk):
    ss = get_object_or_404(CandidateSavedSearch, pk=pk, recruiter=request.user)
    notes = ss.notifications.select_related("candidate").all()
    unread = notes.filter(is_read=False)
    if unread.exists():
        unread.update(is_read=True)
    return render(request, "accounts/candidate_saved_search_notifications.html", {
        "saved_search": ss, "notifications": notes
    })