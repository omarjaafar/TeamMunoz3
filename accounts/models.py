from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    # role choices for user - constants
    JOB_SEEKER = "JOB_SEEKER"
    RECRUITER= "RECRUITER"
    ADMIN= "ADMIN"
    ROLE_CHOICES = [
        (JOB_SEEKER, "Job Seeker"),
        (RECRUITER, "Recruiter"),
        (ADMIN, "Administrator"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=JOB_SEEKER)
    # details that the user fills in to create the profile - each of them will be blank in the start and then the user can
    # fill in stuff. Also it can remain blank if the user chooses to not fill in anything
    headline = models.CharField(max_length=120, blank=True)
    skills = models.TextField(blank=True)
    education = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    links = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} | {self.get_role_display()}"