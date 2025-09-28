from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import Profile
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST


def index(request):
    template_data = {}
    template_data['title'] = 'outdeed'
    return render(request, 'home/index.html', {'template_data': template_data})
    
def about(request):
    template_data = {}
    template_data['title'] = 'About'
    return render(request, 'home/about.html', {'template_data': template_data})

def search(request):
    template_data = {}
    template_data['title'] = 'Search'
    return render(request, 'home/search.html', {'template_data': template_data})

# job seeker
def seeker_apply(request):
    template_data = {}
    template_data['title'] = 'Apply'
    return render(request, 'home/seeker_apply.html', {'template_data': template_data})

def seeker_status(request):
    template_data = {}
    template_data['title'] = 'Application Status'
    return render(request, 'home/seeker_status.html', {'template_data': template_data})

def seeker_settings(request):
    template_data = {}
    template_data['title'] = 'Settings'
    return render(request, 'home/seeker_settings.html', {'template_data': template_data})

@login_required
def seeker_profile(request):
    #this basically allows us to read/write on the same instance throughout that request - no duplicates are created
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # no guard that skips save—always write what was submitted
        # also for cases where the fields are '' (which it is in the start) it doesn't save properly so we look at the format
        # we now directly and explicitly define each of the fields so the data stored in them will have to be saved
        # field_in_profile = (request.POST.get('field') or '').strip()
        # .strip() basically removes the additional whitespace before and after the string
        profile_obj.headline = (request.POST.get('headline') or '').strip()
        profile_obj.skills = (request.POST.get('skills') or '').strip()
        profile_obj.education = (request.POST.get('education') or '').strip()
        profile_obj.experience = (request.POST.get('experience') or '').strip()
        profile_obj.links = (request.POST.get('links') or '').strip()
        profile_obj.save()
        # we now reload the page with the updated object in the database
        return redirect('seeker.profile')   

    template_data = {
        'title': 'Edit Profile',
        'profile': profile_obj,
    }
    return render(request, 'home/seeker_profile.html', {'template_data': template_data})

# ...existing code...

@require_POST
def admin_create_user(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    role = request.POST.get('role')
    if not username or not password or not role:
        messages.error(request, 'All fields are required.')
        return redirect('admin.manage_users')
    if User.objects.filter(username=username).exists():
        messages.error(request, 'Username already exists.')
        return redirect('admin.manage_users')
    user = User.objects.create_user(username=username, password=password)
    if role == 'ADMIN':
        user.is_staff = True
        user.is_superuser = True
        user.save()
    Profile.objects.create(user=user, role=role)
    messages.success(request, f'User {username} created successfully.')
    return redirect('admin.manage_users')

@require_POST
def admin_delete_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    return redirect('admin.manage_users')

# recruiter
def recruiter_post_job(request):
    template_data = {}
    template_data['title'] = 'Post a Job'
    return render(request, 'home/recruiter_post_job.html', {'template_data': template_data})

def recruiter_messages(request):
    template_data = {}
    template_data['title'] = 'Messages'
    return render(request, 'home/recruiter_messages.html', {'template_data': template_data})

# admin
def admin_edit_posts(request):
    template_data = {}
    template_data['title'] = 'Edit Posts'
    return render(request, 'home/admin_edit_posts.html', {'template_data': template_data})

#admin
def admin_manage_users(request):
    users = User.objects.all()
    return render(request, 'home/admin_manage_users.html', {'users': users})

#admin
def change_role(request, user_id, new_role):
    user = User.objects.get(id=user_id)
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.role = new_role
    profile.save()
    return redirect('admin.manage_users')

#admin (POST handler for role change)
from django.views.decorators.http import require_POST

@require_POST
def change_role_post(request, user_id):
    new_role = request.POST.get('role')
    user = User.objects.get(id=user_id)
    profile, _ = Profile.objects.get_or_create(user=user)
    if new_role:
        profile.role = new_role
        profile.save()
        if new_role == 'ADMIN':
            user.is_staff = True
            user.is_superuser = True
            user.save()
        else:
            user.is_staff = False
            user.is_superuser = False
            user.save()
    return redirect('admin.manage_users')