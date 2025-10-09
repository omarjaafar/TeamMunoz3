from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile
from .forms import ProfilePrivacyForm, ProfileEditForm


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
