from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
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

class EmailVerificationCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code_hash = models.CharField(max_length=50)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.PositiveIntegerField(default=0)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    @classmethod
    def expiry_time(cls,minutes=10):
        return timezone.now() + timedelta(minutes=minutes)

class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='following_set')
    following = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='follower_set')
    created_at = models.DateTimeField(auto_now_add=True)