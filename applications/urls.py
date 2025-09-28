from django.urls import path
from .views import MyApplicationsView, manage_applications

app_name = "applications"

urlpatterns = [
    path("mine/", MyApplicationsView.as_view(), name="mine"),
    path("manage/<int:job_id>/", manage_applications, name="manage"),
]
