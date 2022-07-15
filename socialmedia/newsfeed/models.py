from django.db import models
from django.contrib.auth import get_user_model
from socialmedia import users

User = get_user_model()


class Status(models.Model):
    user = models.ForeignKey('users.User', models.CASCADE)
    status_text = models.CharField(max_length=255, null=False, blank=False)
    like = models.IntegerField(default=0)
    dislike = models.IntegerField(default=0)


class VoteTracker(models.Model):
    status = models.ForeignKey('Status', models.CASCADE)
    user = models.ForeignKey('users.User', models.CASCADE)
    vote = models.BooleanField(null=False, blank=False)
