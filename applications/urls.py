from django.urls import path
from .views import MyApplicationsView, manage_applications, recruiter_pipeline, update_application_status

app_name = "applications"

urlpatterns = [
    path("mine/", MyApplicationsView.as_view(), name="mine"),
    path("manage/<int:job_id>/", manage_applications, name="manage"),
    path("pipeline/<int:job_id>/", recruiter_pipeline, name="pipeline"),
    path("update-status/<int:app_id>/<str:new_status>/", update_application_status, name="update_status"),
]
