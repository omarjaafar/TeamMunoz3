from django.db import models
from django.conf import settings
from jobs.models import Job


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = 'APPLIED', 'Applied'
        REVIEW = 'REVIEW', 'Review'
        INTERVIEW = 'INTERVIEW', 'Interview'
        OFFER = 'OFFER', 'Offer'
        CLOSED = 'CLOSED', 'Closed'

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.APPLIED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['job', 'applicant'], name='unique_job_application'),
        ]
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.applicant.username} → {self.job.title} [{self.get_status_display()}]"
