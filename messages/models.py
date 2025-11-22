from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Message(models.Model):
    sender = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='received_messages')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username} | {self.subject}"


class EmailMessage(models.Model):
    sender = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='sent_email_messages')
    recipient_user = models.ForeignKey('auth.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='received_email_messages')
    recipient_email = models.EmailField(max_length=254)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    sent_ok = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        ru = self.recipient_user.username if self.recipient_user else self.recipient_email
        return f"Email from {self.sender.username} to {ru} | {self.subject}"
