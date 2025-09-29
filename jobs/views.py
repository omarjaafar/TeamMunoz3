from django.shortcuts import render, redirect, get_object_or_404
from .models import Job
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from applications.models import Application
from django.urls import reverse
# Create your views here.

@login_required
def index(request):
    #first we go to the jobs table in the database, then give me the rows that are 
    # created by the currently logged in user
    jobs = Job.objects.filter(posted_by=request.user)
    template_data = {
        'title': 'Post a Job',
        'jobs' : jobs
    }
    return render(request, 'jobs/index.html', {'template_data' : template_data})

# pk is a primary key that identifies a specific Job row in the database
# when pk is None, we are creating a new job
# when pk has a value, we edit that existing job
@login_required
def job_form(request, pk=None):
    job = None
    # this checks if a pk for the job currently exists - if it doesn't return 404 error
    # commenting this out would no longer show the data for each of the jobs posted!
    if pk is not None:
        job = get_object_or_404(Job, pk=pk, posted_by=request.user)

    if request.method == 'POST':
        data = request.POST
        fields = {
            'title': (data.get('title') or '').strip(),
            'company': (data.get('company') or '').strip(),
            'location': (data.get('location') or '').strip(),
            'job_type': data.get('job_type') or 'FT',
            'salary': data.get('salary') or None,
            'description': (data.get('description') or '').strip(),
        }

        if job is None:
            #capture the instance, then redirect using its pk - define the fields dict here 
            job = Job.objects.create(posted_by=request.user, **fields)
            return redirect(reverse('jobs.index'), pk=job.pk)

        # update the existing instance, then redirect
        # the for-loop below iterates through the (key, value) pairs in the 'fields' dict
        # for each field name (k) and submitted value (v), we set that attribute on the
        # existing job instance, like setattr(job, 'title', 'New Title')
        for k, v in fields.items():
            setattr(job, k, v)
            job.save()
        return redirect('jobs.index')  

    template_data = {'title': 'Add Job' if job is None else f'Edit: {job.title}', 'job': job}
    return render(request, 'jobs/form.html', {'template_data': template_data})

@login_required
@require_POST
def delete(request, pk):
    # delete only if it belongs to the current user
    deleted_count, _ = Job.objects.filter(pk=pk, posted_by=request.user).delete()
    if deleted_count == 0:
        messages.error(request, "That job wasn't found (or it isn't yours).")
    else:
        messages.success(request, "Job deleted.")
    return redirect('jobs.index')

@login_required
@require_POST
def apply_to_job(request, pk):
    job = get_object_or_404(Job, pk=pk)

    # Prevent recruiters from applying to jobs
    if hasattr(request.user, "profile") and request.user.profile.role != "JOB_SEEKER":
        messages.error(request, "Only job seekers can apply to jobs.")
        return redirect('seeker.apply')

    application, created = Application.objects.get_or_create(
        job=job,
        applicant=request.user,
    )

    if created:
        messages.success(request, f"Successfully applied to {job.title}.")
    else:
        messages.info(request, f"You have already applied to {job.title}.")

    return redirect('seeker.apply')