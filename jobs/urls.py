from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='jobs.index'),
    path('create/', views.job_form, name='jobs.create'),
    path('<int:pk>/edit/', views.job_form, name='jobs.edit'),
    path('<int:pk>/delete/', views.delete, name='jobs.delete'),
    path('<int:pk>/apply/', views.apply_to_job, name='jobs.apply'),
    path('api/jobs/', views.jobs_json, name='jobs.json'),
]