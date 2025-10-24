from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from urllib.parse import parse_qs
from django.db.models import Q
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    JOB_SEEKER = "JOB_SEEKER"
    RECRUITER = "RECRUITER"
    ADMIN = "ADMIN"
    ROLE_CHOICES = [
        (JOB_SEEKER, "Job Seeker"),
        (RECRUITER, "Recruiter"),
        (ADMIN, "Administrator"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=JOB_SEEKER)

    headline = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    skills = models.TextField(blank=True)
    education = models.TextField(blank=True)
    projects = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    links = models.TextField(blank=True)

    show_headline = models.BooleanField(default=True)
    show_location = models.BooleanField(default=True)
    show_skills = models.BooleanField(default=True)
    show_education = models.BooleanField(default=True)
    show_projects = models.BooleanField(default=True)
    show_experience = models.BooleanField(default=True)
    show_links = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} | {self.get_role_display()}"
    
User = settings.AUTH_USER_MODEL

class CandidateSavedSearch(models.Model):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="candidate_saved_searches")
    name = models.CharField(max_length=120, blank=True)
    querystring = models.TextField(blank=True, default="")  # e.g., skills=python&location=GA&exp_min=2
    email_enabled = models.BooleanField(default=True)
    last_checked = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name or f"Candidate Search #{self.pk}"

class CandidateSearchNotification(models.Model):
    saved_search = models.ForeignKey(CandidateSavedSearch, on_delete=models.CASCADE, related_name="notifications")
    candidate = models.ForeignKey("accounts.Profile", on_delete=models.CASCADE, related_name="match_notifications")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("saved_search", "candidate")

# ---- Helper to apply filters from a querystring to a Profile queryset ----
def apply_candidate_querystring_filters(qs_profiles, querystring: str):
    """
    Map simple GET params to Profile filters.
    Expected params:
      - q: free text (matches headline, skills, education)
      - skills: comma/space separated text, substring match
      - location: substring match
      - education: substring match
      - exp_min: integer, minimum years of experience (if you store it)
    """
    params_multi = parse_qs(querystring or "", keep_blank_values=False)
    p = {k: v[0] for k, v in params_multi.items() if v}

    q = (p.get("q") or "").strip()
    if q:
        qs_profiles = qs_profiles.filter(
            Q(headline__icontains=q) |
            Q(skills__icontains=q) |
            Q(education__icontains=q) |
            Q(experience__icontains=q)
        )

    skills = (p.get("skills") or "").strip()
    if skills:
        for token in [t for t in skills.replace(",", " ").split() if t]:
            qs_profiles = qs_profiles.filter(skills__icontains=token)

    location = (p.get("location") or "").strip()
    if location:
        qs_profiles = qs_profiles.filter(location__icontains=location)

    education = (p.get("education") or "").strip()
    if education:
        qs_profiles = qs_profiles.filter(education__icontains=education)

    exp_min = (p.get("exp_min") or "").strip()
    if exp_min.isdigit():
        # If you store numeric years (e.g., profile.years_experience)
        if hasattr(qs_profiles.model, "years_experience"):
            qs_profiles = qs_profiles.filter(years_experience__gte=int(exp_min))
        else:
            # fallback: substring in experience text
            qs_profiles = qs_profiles.filter(experience__icontains=f"{exp_min}")

    # Only job seekers
    qs_profiles = qs_profiles.filter(role="JOB_SEEKER")
    return qs_profiles