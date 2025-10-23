from django.db import models
from django.contrib.auth.models import User
# Create your models here:


#retrieving all users
users = User.objects.all()