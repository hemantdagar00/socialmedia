from django.db import models
from django.contrib.auth import get_user_model
from socialmedia import users

User = get_user_model()


class Status(models.Model):
    user = models.ForeignKey('users.User', models.CASCADE)
    status_photo = models.ImageField(upload_to="upload_image/",null=True, blank=True)
    status_text = models.CharField(max_length=255, null=True, blank=True)
    like = models.IntegerField(default=0)
    dislike = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)


class StatusVoteTracker(models.Model):
    status = models.ForeignKey('Status', models.CASCADE)
    user = models.ForeignKey('users.User', models.CASCADE)
    vote = models.BooleanField(null=False,blank=False)


class Comment(models.Model):
    status = models.ForeignKey('Status', models.CASCADE, null=True, blank=True)
    base_comment = models.ForeignKey("self", models.CASCADE, null=True, blank=True)
    user = models.ForeignKey('users.User', models.CASCADE)
    comment_photo = models.ImageField(upload_to="upload_image/", null=True, blank=True)
    comment_text = models.CharField(max_length=255, null=True, blank=True)
    like = models.IntegerField(default=0)
    dislike = models.IntegerField(default=0)
    comments_on_comment = models.IntegerField(default=0)


class CommentVoteTracker(models.Model):
    comment = models.ForeignKey('Comment', models.CASCADE)
    user = models.ForeignKey('users.User', models.CASCADE)
    vote = models.BooleanField(null=False,blank=False)


class UserRelationDetail(models.Model):
    user = models.ForeignKey('users.User', models.CASCADE, related_name='user', )
    following_list = models.ForeignKey('users.User', models.CASCADE, related_name='following_list', null=True, blank=True)
    follower_list = models.ForeignKey('users.User', models.CASCADE, related_name='follower_list', null=True, blank=True)
    block_list = models.ForeignKey('users.User', models.CASCADE, related_name='block_list', null=True, blank=True)
    req_rx = models.ForeignKey('users.User', models.CASCADE, related_name='req_rx', null=True, blank=True)
    req_sent  = models.ForeignKey('users.User', models.CASCADE, related_name='req_sent', null=True, blank=True)

