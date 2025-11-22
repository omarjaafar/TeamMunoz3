from django.shortcuts import render
from django.http import JsonResponse
from jobs.models import Job  # OR whatever your model is

def jobs_json(request):
    jobs = Job.objects.all()

    data = []
    for job in jobs:
        if job.latitude is not None and job.longitude is not None:
            data.append({
                "id": job.id,
                "title": job.title,
                "description": job.description,
                "latitude": job.latitude,
                "longitude": job.longitude,
            })

    return JsonResponse(data, safe=False)


def gt_map(request):
    return render(request, 'mapview/map.html')