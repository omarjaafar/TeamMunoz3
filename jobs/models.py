from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('FT', 'Full-time'),
        ('PT', 'Part-time'),
        ('IN', 'Internship'),
    ]

    title= models.CharField(max_length=120)
    company = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    job_type= models.CharField(max_length=2, choices=JOB_TYPE_CHOICES, default='FT')
    salary = models.CharField(max_length=120, blank=True)  
    description = models.TextField()

    # this is a feature used by the system to know what jobs a recruiter has posted. it won't be shown to
    # the job seekers 
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')

    def __str__(self):
        return f"{self.title} at {self.company}"