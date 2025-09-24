from django.shortcuts import render, redirect, get_object_or_404
from .models import Job
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
# Create your views here.

@login_required
def index(request):
    #first we go to the jobs table in the database, then give me the rows that are created by the currently
    # logged in user, and sort the order by id
    jobs = Job.objects.filter(posted_by=request.user)
    template_data = {
        'title': 'Post a Job',
        'jobs' : jobs
    }
    return render(request, 'jobs/index.html', {'template_data' : template_data})

@login_required
def job_form(request, pk=None):
    job = None
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
            #capture the instance, then redirect using its pk
            job = Job.objects.create(posted_by=request.user, **fields)
            return redirect('jobs.edit', pk=job.pk)

        # update the existing instance, then redirect
        for k, v in fields.items():
            setattr(job, k, v)
            job.save()
        return redirect('jobs.index')   # or redirect('jobs.index')

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