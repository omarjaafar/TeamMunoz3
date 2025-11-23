from django.shortcuts import render
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required

from jobs.models import Job
from applications.models import Application
from accounts.models import Profile

import math


# ---------------------------------------------------------
# Haversine helper (used for User Story 9)
# ---------------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


# ---------------------------------------------------------
# Existing job map page
# ---------------------------------------------------------
def gt_map(request):
    return render(request, 'mapview/map.html')


# ---------------------------------------------------------
# UPDATED jobs_json — now supports radius filtering
# ---------------------------------------------------------
def jobs_json(request):
    """
    If lat/lng/radius query params are provided, return only jobs
    within the radius. Otherwise return all jobs with coordinates.
    """

    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius")  # km

    # Base queryset
    jobs = Job.objects.exclude(latitude=None).exclude(longitude=None)

    # If no radius search parameters → return all jobs normally
    if not (lat and lng and radius):
        data = []
        for job in jobs:
            data.append({
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "latitude": job.latitude,
                "longitude": job.longitude,
            })
        return JsonResponse(data, safe=False)

    # Convert query values
    lat = float(lat)
    lng = float(lng)
    radius = float(radius)

    # Perform radius filtering
    results = []
    for job in jobs:
        d = haversine(lat, lng, job.latitude, job.longitude)
        if d <= radius:
            results.append({
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "latitude": job.latitude,
                "longitude": job.longitude,
                "distance_km": round(d, 2),
            })

    return JsonResponse(results, safe=False)


# ---------------------------------------------------------
# NEW JSON endpoint for applicant clustering
# ---------------------------------------------------------
@login_required
def applicants_json(request):
    """
    Returns all applicants (with lat/lng) who applied to jobs
    posted by the current recruiter.
    """
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != Profile.RECRUITER:
        return HttpResponseForbidden("Only recruiters can access applicant map data.")

    qs = (
        Application.objects
        .filter(
            job__posted_by=request.user,
            applicant__profile__latitude__isnull=False,
            applicant__profile__longitude__isnull=False,
        )
        .select_related("applicant", "job", "applicant__profile")
    )

    seen = set()
    data = []

    for app in qs:
        applicant = app.applicant
        applicant_profile = applicant.profile

        if applicant.id in seen:
            continue
        seen.add(applicant.id)

        app_count = applicant.applications.filter(job__posted_by=request.user).count()

        data.append({
            "applicant_id": applicant.id,
            "username": applicant.username,
            "headline": applicant_profile.headline,
            "location": applicant_profile.location,
            "latitude": applicant_profile.latitude,
            "longitude": applicant_profile.longitude,
            "applications_count": app_count,
        })

    return JsonResponse(data, safe=False)


# ---------------------------------------------------------
# Recruiter-facing applicant map page
# ---------------------------------------------------------
@login_required
def applicants_map(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != Profile.RECRUITER:
        return HttpResponseForbidden("Only recruiters can view the applicant map.")
    return render(request, 'mapview/applicants_map.html')
