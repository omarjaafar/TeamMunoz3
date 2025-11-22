from django.urls import path
from . import views

urlpatterns = [
    path("", views.gt_map, name="gt_map"),
    path('jobs.json', views.jobs_json, name='jobs_json'),
]