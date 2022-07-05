from urllib import request

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import re
from socialmedia.newsfeed.models import Status, VoteTracker
from socialmedia.users.api.serializers import UserDetailSerializer

User = get_user_model()


class StatusDetailSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")

    class Meta:
        model = Status
        fields = ["id", "user", "status_text", "like", "dislike", "url"]

        extra_kwargs = {
            "url": {"view_name": "api:status-detail", "lookup_field": "id"}
        }


class StatusCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Status
        fields = ["status_text","user"]
        read_only_fields = ("user",)

    def save(self, validated_data):
        status_text = validated_data.pop('status_text')

        instance = Status.objects.create(
            user=self.context['request'].user,
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


class VotesUpdateSerializer(serializers.ModelSerializer):
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

#----------------------------------------------------------------------------------------------

        elif attrs['up_vote'] == True:
            if not VoteTracker.objects.filter(status=self.instance.id).exists():
                self.instance.like += 1
                # update status, user and vote in vote_tracker
                b = VoteTracker.objects.create(status=self.instance, user=self.context['request'].user, vote=True)
                b.save()
            else:
                if not VoteTracker.objects.filter(status=self.instance.id, user=self.context['request'].user).exists():
                    self.instance.like += 1
                    # update status, user and vote in vote_tracker
                    b = VoteTracker.objects.create(status=self.instance, user=self.context['request'].user, vote=True)
                    b.save()
                else:
                    if VoteTracker.objects.get(status=self.instance.id,user=self.context['request'].user).vote == True:
                        raise ValidationError("You already liked the status.")
                    elif VoteTracker.objects.get(status=self.instance.id,user=self.context['request'].user).vote == False:
                        self.instance.like += 1
                        self.instance.dislike -= 1
                        VoteTracker.objects.filter(status=self.instance.id, user=self.context['request'].user).update(vote=True)
#----------------------------------------------------------------------------------------------

        elif attrs['down_vote'] == True:
            if not VoteTracker.objects.filter(status=self.instance.id).exists():
                self.instance.dislike += 1
                # update status, user and vote in vote_tracker
                b = VoteTracker.objects.create(status=self.instance, user=self.context['request'].user, vote=False)
                b.save()
            else:
                if not VoteTracker.objects.filter(status=self.instance.id, user=self.context['request'].user).exists():
                    self.instance.dislike += 1
                    # update status, user and vote in vote_tracker
                    b = VoteTracker.objects.create(status=self.instance, user=self.context['request'].user, vote=False)
                    b.save()
                else:
                    if VoteTracker.objects.get(status=self.instance.id, user=self.context['request'].user).vote == False:
                        raise ValidationError("You already disliked the status.")
                    elif VoteTracker.objects.get(status=self.instance.id,user=self.context['request'].user).vote == True:
                        self.instance.dislike += 1
                        self.instance.like -= 1
                        VoteTracker.objects.filter(status=self.instance.id, user=self.context['request'].user).update(vote=False)
# ----------------------------------------------------------------------------------------------

        elif attrs['up_vote'] == False:
            if VoteTracker.objects.get(status=self.instance.id,user=self.context['request'].user).vote == True:
                VoteTracker.objects.filter(status=self.instance.id,user=self.context['request'].user,vote=True).delete()
                self.instance.like -= 1

        elif attrs['down_vote'] == False:
            if VoteTracker.objects.get(status=self.instance.id,user=self.context['request'].user).vote == False:
                VoteTracker.objects.filter(status=self.instance.id,user=self.context['request'].user,vote=False).delete()
                self.instance.dislike -= 1

# ----------------------------------------------------------------------------------------------
        return attrs

    def update(self, instance, validated_data):
        instance.like = validated_data.get('like', instance.like)
        instance.dislike = validated_data.get('dislike', instance.dislike)
        instance.save()
        return instance

