from urllib import request

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import re
from socialmedia.newsfeed.models import Status, StatusVoteTracker, Comment, CommentVoteTracker
from socialmedia.users.api.serializers import UserDetailSerializer

User = get_user_model()


class StatusDetailSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")
    class Meta:
        model = Status
        fields = ["id", "user", "status_photo", "status_text", "like", "dislike", "comments", "url"]

        extra_kwargs = {
            "url": {"view_name": "api:status-detail", "lookup_field": "id"}
        }


class StatusCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ["status_photo", "status_text","user"]
        read_only_fields = ("user",)

    def validate(self, attrs):
        if (attrs["status_photo"] == None) and (attrs["status_text"] == ""):
            value = False
        elif (attrs["status_photo"] != None) and (attrs["status_text"] == ""):
            value = True
        elif (attrs["status_photo"] == None) and (attrs["status_text"] != ""):
            value = True
        elif (attrs["status_photo"] != None) and (attrs["status_text"] != ""):
            value = True

        if value == False:
            raise ValidationError("Either add a photo or the status.")

        return attrs

    def save(self, validated_data):
        status_text = validated_data.pop('status_text')
        status_photo = validated_data.pop('status_photo')

        instance = Status.objects.create(
            user=self.context['request'].user,
            status_photo=status_photo,
            status_text=status_text,
        )
        return instance


class StatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = ["status_text", ]

    def validate(self, attrs):
        if self.instance.user != self.context['request'].user:
            raise ValidationError("You are not allowed to update the status of other user")
        return attrs

    def update(self, instance, validated_data):
        instance.status_text = validated_data.get('status_text', instance.status_text)
        instance.save()
        return instance


class StatusVotesUpdateSerializer(serializers.ModelSerializer):
    up_vote = serializers.BooleanField(allow_null=True, required=False)
    down_vote = serializers.BooleanField(allow_null=True, required=False)
    class Meta:
        model = Status
        fields = [ "up_vote", "down_vote"]

    def validate(self, attrs):
        if self.instance.user == self.context['request'].user:
            raise ValidationError("You can not like or dislike your own status.")

        elif attrs['up_vote'] == attrs['down_vote'] == None:
            raise ValidationError("Either like it or not.")

        elif attrs['up_vote'] == attrs['down_vote']:
            raise ValidationError("You can not like and dislike the status at same time.")

        elif attrs['up_vote'] == True:
            if not StatusVoteTracker.objects.filter(status=self.instance.id).exists():
                self.instance.like += 1
                # update status, user and vote in vote_tracker
                b = StatusVoteTracker.objects.create(status=self.instance, user=self.context['request'].user, vote=True)
                b.save()
            else:
                if not StatusVoteTracker.objects.filter(status=self.instance.id, user=self.context['request'].user).exists():
                    self.instance.like += 1
                    # update status, user and vote in vote_tracker
                    b = StatusVoteTracker.objects.create(status=self.instance, user=self.context['request'].user, vote=True)
                    b.save()
                else:
                    if StatusVoteTracker.objects.get(status=self.instance.id,user=self.context['request'].user).vote == True:
                        raise ValidationError("You already liked the status.")
                    elif StatusVoteTracker.objects.get(status=self.instance.id,user=self.context['request'].user).vote == False:
                        self.instance.like += 1
                        self.instance.dislike -= 1
                        StatusVoteTracker.objects.filter(status=self.instance.id, user=self.context['request'].user).update(vote=True)

        elif attrs['down_vote'] == True:
            if not StatusVoteTracker.objects.filter(status=self.instance.id).exists():
                self.instance.dislike += 1
                # update status, user and vote in vote_tracker
                b = StatusVoteTracker.objects.create(status=self.instance, user=self.context['request'].user, vote=False)
                b.save()
            else:
                if not StatusVoteTracker.objects.filter(status=self.instance.id, user=self.context['request'].user).exists():
                    self.instance.dislike += 1
                    # update status, user and vote in vote_tracker
                    b = StatusVoteTracker.objects.create(status=self.instance, user=self.context['request'].user, vote=False)
                    b.save()
                else:
                    if StatusVoteTracker.objects.get(status=self.instance.id, user=self.context['request'].user).vote == False:
                        raise ValidationError("You already disliked the status.")
                    elif StatusVoteTracker.objects.get(status=self.instance.id,user=self.context['request'].user).vote == True:
                        self.instance.dislike += 1
                        self.instance.like -= 1
                        StatusVoteTracker.objects.filter(status=self.instance.id, user=self.context['request'].user).update(vote=False)

        elif attrs['up_vote'] == False:
            if StatusVoteTracker.objects.get(status=self.instance.id,user=self.context['request'].user).vote == True:
                StatusVoteTracker.objects.filter(status=self.instance.id,user=self.context['request'].user,vote=True).delete()
                self.instance.like -= 1

        elif attrs['down_vote'] == False:
            if StatusVoteTracker.objects.get(status=self.instance.id,user=self.context['request'].user).vote == False:
                StatusVoteTracker.objects.filter(status=self.instance.id,user=self.context['request'].user,vote=False).delete()
                self.instance.dislike -= 1

        return attrs

    def update(self, instance, validated_data):
        instance.like = validated_data.get('like', instance.like)
        instance.dislike = validated_data.get('dislike', instance.dislike)
        instance.save()
        return instance


class CommentDetailSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")

    class Meta:
        model = Comment
        fields = ["id", "status", "base_comment", "user", "comment_photo", "comment_text", "like", "dislike", "comments_on_comment", "url"]

        extra_kwargs = {
                    "url": {"view_name": "api:comment-detail", "lookup_field": "id"}
                }



class CommentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ["status", "base_comment", "comment_photo", "comment_text","user"]
        read_only_fields = ("user",)

    def validate(self, attrs):
        if (attrs["status"] != None) and (attrs["base_comment"] != None):
            value = False
        elif (attrs["status"] == None) and (attrs["base_comment"] == None):
            value = False
        elif (attrs["status"] != None) and (attrs["base_comment"] == None):
            value = True
        elif (attrs["status"] == None) and (attrs["base_comment"] != None):
            value = True

        if value == False:
            raise ValidationError("You are allowed to either comment on a Status or on a Comment")

        if (attrs["comment_photo"] == None) and (attrs["comment_text"] == ""):
            value = False
        elif (attrs["comment_photo"] != None) and (attrs["comment_text"] == ""):
            value = True
        elif (attrs["comment_photo"] == None) and (attrs["comment_text"] != ""):
            value = True
        elif (attrs["comment_photo"] != None) and (attrs["comment_text"] != ""):
            value = True

        if value == False:
            raise ValidationError("Either add a photo or the comment.")

        return attrs

    def save(self, validated_data):
        status = validated_data.pop('status')
        base_comment = validated_data.pop('base_comment')
        comment_text = validated_data.pop('comment_text')
        comment_photo = validated_data.pop('comment_photo')

        if status == None:
            status = Comment.objects.get(id=base_comment.id).status

        instance = Comment.objects.create(
            status=status,
            base_comment=base_comment,
            user=self.context['request'].user,
            comment_photo=comment_photo,
            comment_text=comment_text,
        )
        return instance


class CommentUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ["comment_text", ]

    def validate(self, attrs):
        if self.instance.user != self.context['request'].user:
            raise ValidationError("You are not allowed to update the comment of other user")
        return attrs

    def update(self, instance, validated_data):
        instance.comment_text = validated_data.get('comment_text', instance.comment_text)
        instance.save()
        return instance


class CommentVotesUpdateSerializer(serializers.ModelSerializer):
    up_vote = serializers.BooleanField(allow_null=True, required=False)
    down_vote = serializers.BooleanField(allow_null=True, required=False)
    class Meta:
        model = Comment
        fields = [ "up_vote", "down_vote"]

    def validate(self, attrs):
        if self.instance.user == self.context['request'].user:
            raise ValidationError("You can not like or dislike your own comment.")

        elif attrs['up_vote'] == attrs['down_vote'] == None:
            raise ValidationError("Either like it or not.")

        elif attrs['up_vote'] == attrs['down_vote']:
            raise ValidationError("You can not like and dislike the status at same time.")

        elif attrs['up_vote'] == True:
            if not CommentVoteTracker.objects.filter(comment=self.instance.id).exists():
                self.instance.like += 1
                # update status, user and vote in vote_tracker
                b = CommentVoteTracker.objects.create(comment=self.instance, user=self.context['request'].user, vote=True)
                b.save()
            else:
                if not CommentVoteTracker.objects.filter(comment=self.instance.id, user=self.context['request'].user).exists():
                    self.instance.like += 1
                    # update status, user and vote in vote_tracker
                    b = CommentVoteTracker.objects.create(comment=self.instance, user=self.context['request'].user, vote=True)
                    b.save()
                else:
                    if CommentVoteTracker.objects.get(comment=self.instance.id,user=self.context['request'].user).vote == True:
                        raise ValidationError("You already liked the comment.")
                    elif CommentVoteTracker.objects.get(comment=self.instance.id,user=self.context['request'].user).vote == False:
                        self.instance.like += 1
                        self.instance.dislike -= 1
                        CommentVoteTracker.objects.filter(comment=self.instance.id, user=self.context['request'].user).update(vote=True)

        elif attrs['down_vote'] == True:
            if not CommentVoteTracker.objects.filter(comment=self.instance.id).exists():
                self.instance.dislike += 1
                # update status, user and vote in vote_tracker
                b = CommentVoteTracker.objects.create(comment=self.instance, user=self.context['request'].user, vote=False)
                b.save()
            else:
                if not CommentVoteTracker.objects.filter(comment=self.instance.id, user=self.context['request'].user).exists():
                    self.instance.dislike += 1
                    # update status, user and vote in vote_tracker
                    b = CommentVoteTracker.objects.create(comment=self.instance, user=self.context['request'].user, vote=False)
                    b.save()
                else:
                    if CommentVoteTracker.objects.get(comment=self.instance.id, user=self.context['request'].user).vote == False:
                        raise ValidationError("You already disliked the comment.")
                    elif CommentVoteTracker.objects.get(comment=self.instance.id,user=self.context['request'].user).vote == True:
                        self.instance.dislike += 1
                        self.instance.like -= 1
                        CommentVoteTracker.objects.filter(comment=self.instance.id, user=self.context['request'].user).update(vote=False)

        elif attrs['up_vote'] == False:
            if CommentVoteTracker.objects.get(comment=self.instance.id,user=self.context['request'].user).vote == True:
                CommentVoteTracker.objects.filter(comment=self.instance.id,user=self.context['request'].user,vote=True).delete()
                self.instance.like -= 1

        elif attrs['down_vote'] == False:
            if CommentVoteTracker.objects.get(comment=self.instance.id,user=self.context['request'].user).vote == False:
                CommentVoteTracker.objects.filter(comment=self.instance.id,user=self.context['request'].user,vote=False).delete()
                self.instance.dislike -= 1

        return attrs

    def update(self, instance, validated_data):
        instance.like = validated_data.get('like', instance.like)
        instance.dislike = validated_data.get('dislike', instance.dislike)
        instance.save()
        return instance





