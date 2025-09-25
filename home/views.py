from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import Profile

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