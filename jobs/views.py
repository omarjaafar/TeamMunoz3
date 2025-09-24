from django.shortcuts import render, redirect
from .models import Job
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required
def index(request):
    #first we go to the jobs table in the database, then give me the rows that are created by the currently
    # logged in user, and sort the order by id
    jobs = Job.objects.filter(posted_by=request.user).order_by('id')
    template_data = {
        'title': 'Post a Job',
        'jobs' : jobs
    }
    return render(request, 'jobs/index.html', {'template_data' : template_data})

@login_required
def job_form(request, pk=None):
    job = None

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
            Job.objects.create(posted_by=request.user, **fields)
        else:
            for k, v in fields.items():
                setattr(job, k, v)
            job.save()
        return redirect('jobs.index')  


    template_data = {
    'title': 'Add Job' if job is None else f'Edit: {job.title}',
    'job': job,
    }
    return render(request, 'jobs/form.html', {'template_data': template_data})