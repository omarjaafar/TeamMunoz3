from django.db import models
from django.contrib.auth.models import User

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
