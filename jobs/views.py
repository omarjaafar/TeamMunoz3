from django.shortcuts import render, redirect, get_object_or_404
from .models import Job
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from applications.models import Application
from django.http import JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from math import radians, sin, cos, sqrt, asin

# Helper to safely parse floats from POST
def safe_float(value):
    try:
        if value is None or value == '':
            return None
        return float(value)
    except (ValueError, TypeError):
        return None

# Create your views here.

@login_required
def index(request):
    # first we go to the jobs table in the database, then give me the rows that are 
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
    if pk is not None:
        job = get_object_or_404(Job, pk=pk, posted_by=request.user)

    if request.method == 'POST':
        data = request.POST
        # parse lat/lng safely
        lat = safe_float(data.get('latitude'))
        lng = safe_float(data.get('longitude'))

        fields = {
            'title': (data.get('title') or '').strip(),
            'company': (data.get('company') or '').strip(),
            'location': (data.get('location') or '').strip(),
            'job_type': data.get('job_type') or 'FT',
            'salary': data.get('salary') or None,
            'description': (data.get('description') or '').strip(),
            # include lat/lng so they are saved/updated when provided (None is fine)
            'latitude': lat,
            'longitude': lng,
        }

        if job is None:
            # create new job with lat/lng included
            job = Job.objects.create(posted_by=request.user, **fields)
            # redirect to index after create (original code tried to pass pk incorrectly)
            return redirect('jobs.index')

        # update existing instance fields, save once after loop
        for k, v in fields.items():
            setattr(job, k, v)
        job.save()
        return redirect('jobs.index')  

    template_data = {'title': 'Add Job' if job is None else f'Edit: {job.title}', 'job': job}
    return render(request, 'jobs/form.html', {'template_data': template_data})


def haversine_km(lat1, lon1, lat2, lon2):
    # Earth radius in km
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def jobs_json(request):
    """
    GET params:
    lat (float), lng (float), radius (km, float)  -> optional
    Returns JSON list of jobs (optionally filtered by radius), each with distance (km).
    """
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius")  # km

    qs = Job.objects.filter(latitude__isnull=False, longitude__isnull=False)

    # If lat/lng/radius provided, compute distances and filter.
    if lat is not None and lng is not None and radius is not None:
        try:
            lat = float(lat); lng = float(lng); radius = float(radius)
        except ValueError:
            return HttpResponseBadRequest("lat, lng and radius must be numeric") #if given wrong information
        results = []
        for job in qs:
            d = haversine_km(lat, lng, job.latitude, job.longitude)
            if d <= radius:
                results.append({
                    "id": job.id,
                    "title": job.title,
                    "description": job.description,
                    "latitude": job.latitude,
                    "longitude": job.longitude,
                    "distance_km": round(d, 3),
                })
        # sort by distance
        results.sort(key=lambda x: x["distance_km"])
        return JsonResponse(results, safe=False)

    # Otherwise return all jobs (careful if many)
    results = [{
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "latitude": job.latitude,
        "longitude": job.longitude,
    } for job in qs]
    return JsonResponse(results, safe=False)

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

    note = (request.POST.get("note") or "").strip()
    application, created = Application.objects.get_or_create(
        job=job,
        applicant=request.user,
        defaults={"notes": note}
    )

    if created:
        messages.success(request, f"Successfully applied to {job.title}.")
    else:
        # If they re-apply with a new note, update (your choice)
        if note:
            application.notes = note
            application.save(update_fields=["notes"])
            messages.success(request, "Your note was updated for this application.")
        else:
            messages.info(request, "You already applied to this job.")


    return redirect('seeker.apply')