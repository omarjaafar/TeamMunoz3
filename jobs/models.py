from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Job(models.Model):
    JOB_TYPE_CHOICES = [
        ('FT', 'Full-time'),
        ('PT', 'Part-time'),
        ('IN', 'Internship'),
    ]
    REMOTE_ONSITE_CHOICES = [
        ('R', 'Remote'),
        ('O', 'Onsite'),
    ]
    VISA_SPONSORSHIP_CHOICES = [
        ('Y', 'Yes'),
        ('N', 'No'),
    ]
    title= models.CharField(max_length=120)
    company = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    job_type= models.CharField(max_length=2, choices=JOB_TYPE_CHOICES, default='FT')
    salary = models.CharField(max_length=120, blank=True)  
    description = models.TextField()
    remote_onsite = models.CharField(max_length=1, choices=REMOTE_ONSITE_CHOICES, default='O')
    visa_sponsorship = models.CharField(max_length=1, choices=VISA_SPONSORSHIP_CHOICES, default='N')
    
    #for map purposes
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # every recruiter posts jobs. we get the jobs that are posted by that recruiter.
    # if the recruiter no longer exists, then all the jobs posted by them will also be deleted (on_delete=...)
    # the last 2 just set the column vals to NULL if there have been no job posted
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)         

    # tiemstamps for job postings
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)     

    # the name that should be returned should be of the form "Recruiter at Company"
    def __str__(self):
        return f"{self.title} at {self.company}"

    