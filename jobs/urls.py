from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='jobs.index'),
    path('create/', views.job_form, name='jobs.create'),
    path('<int:pk>/edit/', views.job_form, name='jobs.edit'),
    path('<int:pk>/delete/', views.delete, name='jobs.delete'),
]