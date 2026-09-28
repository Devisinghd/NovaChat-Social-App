from django.db import models
from django.contrib.auth.models import User

from django.conf import settings
# Create your models here.

class Profile(models.Model):

    class GenderChoices(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'
        PREFER_NOT_TO_SAY = 'P', 'Prefer not to say'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    gender = models.CharField(max_length=1, choices=GenderChoices, default=GenderChoices.PREFER_NOT_TO_SAY,)
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True)
    website = models.URLField(max_length=500,blank=True,null=True)

    def __str__(self):
        return self.user.username
