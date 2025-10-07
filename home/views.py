from django.shortcuts import render, redirect, get_object_or_404 #
from django.contrib.auth.decorators import login_required, user_passes_test #
from accounts.models import Profile
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
import re
from jobs.models import Job
from applications.views import MyApplicationsView  # ✅ import our applications view


def index(request):
    #i think we could also write it like templaye_data = {'title': 'outdeed'}
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
    from django.db.models import Q
    import re
    
    # Get all jobs initially
    jobs = Job.objects.all()
    
    # Apply filters based on GET parameters
    search_query = request.GET.get('search', '')
    job_type = request.GET.get('job_type', '')
    location = request.GET.get('location', '')
    remote_onsite = request.GET.get('remote_onsite', '')
    visa_sponsorship = request.GET.get('visa_sponsorship', '')
    salary_range = request.GET.get('salary_range', '')
    
    # Apply search filter
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(company__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply job type filter
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    # Apply location filter
    if location:
        jobs = jobs.filter(location__icontains=location)
    
    # Apply remote/onsite filter
    if remote_onsite:
        jobs = jobs.filter(remote_onsite=remote_onsite)
    
    # Apply visa sponsorship filter
    if visa_sponsorship:
        jobs = jobs.filter(visa_sponsorship=visa_sponsorship)
    
    # Apply salary range filter
    if salary_range:
        if salary_range == '0-30000':
            jobs = jobs.filter(
                Q(salary__icontains='0') | Q(salary__icontains='1') | Q(salary__icontains='2') |
                Q(salary__icontains='3') | Q(salary__icontains='4') | Q(salary__icontains='5') |
                Q(salary__icontains='6') | Q(salary__icontains='7') | Q(salary__icontains='8') |
                Q(salary__icontains='9')
            ).exclude(
                Q(salary__icontains='40') | Q(salary__icontains='50') | Q(salary__icontains='60') |
                Q(salary__icontains='70') | Q(salary__icontains='80') | Q(salary__icontains='90') |
                Q(salary__icontains='100') | Q(salary__icontains='150')
            )
        elif salary_range == '30000-50000':
            jobs = jobs.filter(
                Q(salary__icontains='30') | Q(salary__icontains='35') | Q(salary__icontains='40') |
                Q(salary__icontains='45') | Q(salary__icontains='50')
            )
        elif salary_range == '50000-75000':
            jobs = jobs.filter(
                Q(salary__icontains='50') | Q(salary__icontains='55') | Q(salary__icontains='60') |
                Q(salary__icontains='65') | Q(salary__icontains='70') | Q(salary__icontains='75')
            )
        elif salary_range == '75000-100000':
            jobs = jobs.filter(
                Q(salary__icontains='75') | Q(salary__icontains='80') | Q(salary__icontains='85') |
                Q(salary__icontains='90') | Q(salary__icontains='95') | Q(salary__icontains='100')
            )
        elif salary_range == '100000-150000':
            jobs = jobs.filter(
                Q(salary__icontains='100') | Q(salary__icontains='110') | Q(salary__icontains='120') |
                Q(salary__icontains='130') | Q(salary__icontains='140') | Q(salary__icontains='150')
            )
        elif salary_range == '150000+':
            jobs = jobs.filter(
                Q(salary__icontains='150') | Q(salary__icontains='200') | Q(salary__icontains='250') |
                Q(salary__icontains='300') | Q(salary__icontains='500')
            )
    
    # Build simple recommendations based on the seeker's profile
    recommended_jobs = Job.objects.none()
    try:
        profile = request.user.profile if request.user.is_authenticated else None
    except Exception:
        profile = None

    if profile is not None:
        profile_location = (profile.location or '').strip()
        # normalize skills to a list of keywords
        raw_skills = (profile.skills or '')
        # split by comma or newline and lowercase/strip
        skill_tokens = [s.strip().lower() for s in re.split(r"[,\n]", raw_skills) if s.strip()]

        skill_query = Q()
        for token in skill_tokens[:8]:  # limit to first 8 tokens for efficiency
            skill_query |= Q(title__icontains=token) | Q(description__icontains=token)

        loc_query = Q()
        if profile_location:
            loc_query = Q(location__icontains=profile_location)

        # Prefer matches on both location and skills; optionally fallback to skills only
        if skill_tokens or profile_location:
            qs_skill = Job.objects.filter(skill_query)
            qs_both = qs_skill.filter(loc_query) if profile_location else Job.objects.none()

            # Build ordered list in Python 
            recommended_list = list(qs_both.order_by('-created_at')[:6])
            # Only fill with skills-only if the user actually provided skills
            if skill_tokens and len(recommended_list) < 6:
                taken_ids = [j.id for j in recommended_list]
                more = list(
                    qs_skill.exclude(id__in=taken_ids).order_by('-created_at')[: 6 - len(recommended_list)]
                )
                recommended_list.extend(more)

            if recommended_list:
                recommended_jobs = recommended_list
            else:
                recommended_jobs = []
        else:
            # no profile signals: no recommendations
            recommended_jobs = []
    else:
        # anonymous users: no recommendations
        recommended_jobs = []

    template_data = {
        'title': 'Apply',
        'jobs': jobs,
        'recommended_jobs': recommended_jobs,
    }
    return render(request, 'home/seeker_apply.html', {'template_data': template_data})


# ✅ Removed old seeker_status function
# Instead, seeker.status is now wired in urls.py to MyApplicationsView


def seeker_settings(request):
    template_data = {}
    template_data['title'] = 'Settings'
    return render(request, 'home/seeker_settings.html', {'template_data': template_data})

@login_required
def seeker_profile(request):
    profile_obj, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile_obj.headline = (request.POST.get('headline') or '').strip()
        profile_obj.location = (request.POST.get('location') or '').strip()
        profile_obj.skills = (request.POST.get('skills') or '').strip()
        profile_obj.education = (request.POST.get('education') or '').strip()
        profile_obj.projects = (request.POST.get('projects') or '').strip()
        profile_obj.experience = (request.POST.get('experience') or '').strip()
        profile_obj.links = (request.POST.get('links') or '').strip()
        profile_obj.save()
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

# recruiter: find candidates
def is_recruiter(user):
    return user.is_authenticated and (
        hasattr(user, "profile") and getattr(user.profile, "role", None) == "RECRUITER"
    )

@login_required
@user_passes_test(is_recruiter)
def recruiter_find_candidates(request):
    from django.db.models import Q

    skills_q = (request.GET.get('skills') or '').strip()
    location_q = (request.GET.get('location') or '').strip()
    projects_q = (request.GET.get('projects') or '').strip()

    candidates = Profile.objects.filter(role=Profile.JOB_SEEKER)

    query = Q()
    if skills_q:
        for token in [t.strip() for t in re.split(r"[,\n]", skills_q) if t.strip()]:
            query |= Q(skills__icontains=token)
    if location_q:
        query &= Q(location__icontains=location_q)
    if projects_q:
        for token in [t.strip() for t in re.split(r"[,\n]", projects_q) if t.strip()]:
            query &= Q(projects__icontains=token)

    if skills_q or location_q or projects_q:
        candidates = candidates.filter(query)

    candidates = candidates.select_related('user').order_by('user__username')

    template_data = {
        'title': 'Find Candidates',
        'candidates': candidates,
    }
    return render(request, 'home/recruiter_search_candidates.html', {'template_data': template_data})

# admin

def is_admin(user):
    """
    Reusable admin check.
    """
    return user.is_authenticated and (
        getattr(user, "is_staff", False) or
        (hasattr(user, "profile") and getattr(user.profile, "role", None) == "ADMIN")
    )

@login_required
@user_passes_test(is_admin)
def admin_edit_posts(request):
    # list all jobs for admin
    template_data = {
        'title': 'Edit Posts',
        'posts': Job.objects.all().order_by('-created_at')  # use correct timestamp field
    }
    return render(request, 'home/admin_edit_posts.html', {'template_data': template_data})

#admin
def admin_manage_users(request):
    template_data = {
        'title': 'Manage Users',
        'users': User.objects.all().order_by('username')
    }
    return render(request, 'home/admin_manage_users.html', {'template_data': template_data})

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
    user = get_object_or_404(User, id=user_id)
    profile, _ = Profile.objects.get_or_create(user=user)
    if new_role:
        profile.role = new_role
        profile.save()
        if new_role == 'ADMIN':
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False
        user.save()
    return redirect('admin.manage_users')

@login_required
@user_passes_test(is_admin)
def admin_edit_post(request, pk):
    # open the existing job in the form template (jobs/forms.html)
    job = get_object_or_404(Job, pk=pk)

    if request.method == 'POST':
        # Update fields manually to match your jobs/forms.html inputs:
        job.title = (request.POST.get('title') or '').strip()
        job.company = (request.POST.get('company') or '').strip()
        job.location = (request.POST.get('location') or '').strip()
        job.job_type = request.POST.get('job_type') or job.job_type
        salary = request.POST.get('salary')
        job.salary = float(salary) if salary not in (None, '') else None
        job.description = (request.POST.get('description') or '').strip()
        job.remote_onsite = request.POST.get('remote_onsite') or job.remote_onsite
        job.visa_sponsorship = request.POST.get('visa_sponsorship') or job.visa_sponsorship
        job.save()
        messages.success(request, "Job updated.")
        return redirect('admin.edit_posts')

    template_data = {
        'title': f'Edit Job — {job.title}',
        'job': job
    }
    # reuse your existing job form template
    return render(request, 'jobs/form.html', {'template_data': template_data})


@login_required
@user_passes_test(is_admin)
def admin_delete_post(request, pk):
    post = get_object_or_404(Job, pk=pk)
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Job deleted.")
        return redirect('admin.edit_posts')

    # simple confirmation page
    template_data = {'title': 'Confirm Delete', 'post': post}
    return render(request, 'home/admin_confirm_delete.html', {'template_data': template_data})