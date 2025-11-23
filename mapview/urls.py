from django.urls import path
from . import views

urlpatterns = [
    path("", views.gt_map, name="gt_map"),
    path("jobs.json", views.jobs_json, name="jobs_json"),
    path("applicants.json", views.applicants_json, name="applicants_json"),  # JSON feed
    path("applicants/", views.applicants_map, name="applicants_map"),        # NEW recruiter map page
]
