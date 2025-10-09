from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Application
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from jobs.models import Job
from .forms import ApplicationStatusForm  # <-- new import
from django.http import JsonResponse



class MyApplicationsView(LoginRequiredMixin, ListView):
    template_name = "home/seeker_status.html"
    context_object_name = "applications"

    def get_queryset(self):
        return Application.objects.select_related("job").filter(applicant=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["template_data"] = {"title": "My Applications"}
        return ctx


@login_required
def manage_applications(request, job_id):
    # only recruiters can view/manage applications
    if not hasattr(request.user, "profile") or request.user.profile.role != "RECRUITER":
        messages.error(request, "Only recruiters can manage applications.")
        return redirect("home.index")

    job = get_object_or_404(Job, pk=job_id, posted_by=request.user)
    applications = Application.objects.filter(job=job).select_related("applicant")

    if request.method == "POST":
        app_id = request.POST.get("app_id")
        application = get_object_or_404(Application, pk=app_id, job=job)
        form = ApplicationStatusForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, f"Updated status for {application.applicant.username}.")
            return redirect("applications:manage", job_id=job.id)
    else:
        form = ApplicationStatusForm()

    template_data = {
        "title": f"Manage Applications for {job.title}",
        "job": job,
        "applications": applications,
        "form": form,
    }
    return render(request, "applications/manage.html", {"template_data": template_data})


# --- NEW: Recruiter pipeline (read-only Kanban board) ---
@login_required
def recruiter_pipeline(request, job_id):
    if not hasattr(request.user, "profile") or request.user.profile.role != "RECRUITER":
        messages.error(request, "Only recruiters can view pipelines.")
        return redirect("home.index")

    job = get_object_or_404(Job, pk=job_id, posted_by=request.user)
    applications = Application.objects.filter(job=job).select_related("applicant__profile")

    # group applications by status
    pipeline = {
        "APPLIED": applications.filter(status="APPLIED"),
        "REVIEW": applications.filter(status="REVIEW"),
        "INTERVIEW": applications.filter(status="INTERVIEW"),
        "OFFER": applications.filter(status="OFFER"),
        "CLOSED": applications.filter(status="CLOSED"),
    }

    template_data = {
        "title": f"{job.title} – Pipeline",
        "job": job,
        "pipeline": pipeline,
    }
    return render(request, "applications/recruiter_pipeline.html", {"template_data": template_data})

@login_required
def update_application_status(request, app_id, new_status):
    if not hasattr(request.user, "profile") or request.user.profile.role != "RECRUITER":
        return JsonResponse({"success": False, "error": "Unauthorized"}, status=403)

    try:
        app = Application.objects.get(id=app_id)
        app.status = new_status
        app.save()
        return JsonResponse({"success": True})
    except Application.DoesNotExist:
        return JsonResponse({"success": False, "error": "Not found"}, status=404)