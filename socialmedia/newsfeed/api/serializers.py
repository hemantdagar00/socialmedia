from urllib import request

from django.contrib.auth import get_user_model, models
from django.contrib.auth.hashers import make_password
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import re
from socialmedia.newsfeed.models import Status, StatusVoteTracker, Comment, CommentVoteTracker, UserRelationDetail
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

        elif not (UserRelationDetail.objects.filter(user=self.context['request'].user.id,
                                                 following_list=self.instance.user.id).exists()):
            raise ValidationError("This status not exist/ because you do not follow the user of the status.")

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
            raise ValidationError("Atleast add a photo or the comment.")

        return attrs

    def save(self, validated_data):
        status = validated_data.pop('status')
        base_comment = validated_data.pop('base_comment')
        comment_text = validated_data.pop('comment_text')
        comment_photo = validated_data.pop('comment_photo')

        if status == None:
            if not (UserRelationDetail.objects.filter(user=self.context['request'].user.id,
                                                      following_list=base_comment.user.id).exists()):
                if not (self.context['request'].user.id == base_comment.user.id):
                    raise ValidationError("This base_comment not exist/ because you do not follow the user of the base_comment.")

            elif not (UserRelationDetail.objects.filter(user=self.context['request'].user.id,
                                                      following_list=base_comment.status.user.id).exists()):
                if not (self.context['request'].user.id == base_comment.status.user.id):
                    raise ValidationError("This status not exist/ because you do not follow the user of the status.")

        else:
            if not (UserRelationDetail.objects.filter(user=self.context['request'].user.id,
                                                        following_list=status.user.id).exists()):
                if not (self.context['request'].user.id == status.user.id):
                    raise ValidationError("This status not exist/ because you do not follow the user of the status.")

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

        elif not (UserRelationDetail.objects.filter(user=self.context['request'].user.id,
                                                 following_list=self.instance.user.id).exists()):
            raise ValidationError("This 'comment' is not exist(or you do not follow the user of the 'comment').")

        elif not (UserRelationDetail.objects.filter(user=self.context['request'].user.id,
                                                        following_list=self.instance.base_comment.user.id).exists()):
            if not (self.context['request'].user.id == self.instance.base_comment.user.id):
                raise ValidationError("This 'base_comment' is not exist(or you do not follow the user of the 'base_comment').")

        elif not (UserRelationDetail.objects.filter(user=self.context['request'].user.id,
                                                        following_list=self.instance.status.user.id).exists()):
            if not (self.context['request'].user.id == self.instance.status.user.id):
                raise ValidationError("This 'status' is not exist(or you do not follow the user of the 'status').")

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


#-----------------------------------------------------------------------------------

class UserRelationDetailDetailSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")
    user_list = serializers.SerializerMethodField()

    def get_user_list(self, obj):
        user_list = []
        for user in User.objects.all():
            user_list.append(
                {
                    'id':user.id,
                    'username':user.username,
                    'no_of_status':Status.objects.filter(user=user.id).count(),
                    'no_of_followings':UserRelationDetail.objects.filter(user=user.id).exclude(following_list=None).values_list('following_list', flat=True).count(),
                    'no_of_followers':UserRelationDetail.objects.filter(user=user.id).exclude(follower_list=None).values_list('follower_list', flat=True).count(),
                    'no_of_blocked_users': UserRelationDetail.objects.filter(user=user.id).exclude(block_list=None).values_list('block_list', flat=True).count(),
                    'no_of_req_rx': UserRelationDetail.objects.filter(user=user.id).exclude(req_rx=None).values_list('req_rx', flat=True).count(),
                    'no_of_req_sent': UserRelationDetail.objects.filter(user=user.id).exclude(req_sent=None).values_list('req_sent', flat=True).count(),

                }
            )
        return user_list

    class Meta:
        model = UserRelationDetail
        fields = ["id", "user", "following_list", "follower_list", "block_list", "req_rx", "req_sent", "url", "user_list"]

        extra_kwargs = {
            "url": {"view_name": "api:userrelationdetail-detail", "lookup_field": "id"}
        }


class UserFollowSerializer(serializers.ModelSerializer):
    user2 = serializers.IntegerField(allow_null=False)

    class Meta:
        model = UserRelationDetail
        fields = ['user', 'user2']
        read_only_fields = ("user",)

    def validate(self, attrs):
        if (attrs["user2"] == self.context['request'].user):
            raise ValidationError("You can not follow yourself.")
        elif (UserRelationDetail.objects.filter(user=attrs["user2"] ,block_list=self.context['request'].user.id).exists()):
            raise ValidationError("You have been blocked by this user/ this user is not exist.")
        elif (UserRelationDetail.objects.filter(user=self.context['request'].user.id ,block_list=attrs["user2"]).exists()):
            raise ValidationError("You blocked this user.")
        elif (UserRelationDetail.objects.filter(user=self.context['request'].user.id ,req_sent=attrs["user2"]).exists()):
            raise ValidationError("You already sent request to this user.")

        return attrs

    def save(self, validated_data):
        id = validated_data.pop('user2')
        user2 = User.objects.get(id=id)

        instance = UserRelationDetail.objects.create(
            user=self.context['request'].user,
            req_sent=user2,
        )

        UserRelationDetail.objects.create(
            user=user2,
            req_rx=self.context['request'].user,
        )

        return instance


class UserUnfollowSerializer(serializers.ModelSerializer):
    user2 = serializers.IntegerField(allow_null=False)

    class Meta:
        model = UserRelationDetail
        fields = ['user', 'user2']
        read_only_fields = ("user",)

    def validate(self, attrs):
        if (attrs["user2"] == self.context['request'].user):
            raise ValidationError("You can not unfollow yourself.")
        elif (UserRelationDetail.objects.filter(user=attrs["user2"] ,block_list=self.context['request'].user.id).exists()):
            raise ValidationError("You have been blocked by this user/ this user is not exist.")
        elif (UserRelationDetail.objects.filter(user=self.context['request'].user.id ,block_list=attrs["user2"]).exists()):
            raise ValidationError("You blocked this user.")
        elif not (UserRelationDetail.objects.filter(user=self.context['request'].user.id,
                                                following_list=attrs["user2"]).exists()):
            raise ValidationError("You did not follow this user.")

        return attrs

    def save(self, validated_data):
        id = validated_data.pop('user2')
        user2 = User.objects.get(id=id)


        instance = UserRelationDetail.objects.all()

        UserRelationDetail.objects.filter(
            user=self.context['request'].user,
            following_list=user2,
        ).delete()

        UserRelationDetail.objects.filter(
            user=user2,
            follower_list=self.context['request'].user,
        ).delete()

        return instance


class UserRemoveFollowerSerializer(serializers.ModelSerializer):
    user2 = serializers.IntegerField(allow_null=False)
    class Meta:
        model = UserRelationDetail
        fields = ['user', 'user2']
        read_only_fields = ("user",)

    def validate(self, attrs):
        if (attrs["user2"] == self.context['request'].user):
            raise ValidationError("You can not unfollow yourself.")
        elif (UserRelationDetail.objects.filter(user=attrs["user2"] ,block_list=self.context['request'].user.id).exists()):
            raise ValidationError("You have been blocked by this user/ this user is not exist.")
        elif (UserRelationDetail.objects.filter(user=self.context['request'].user.id ,block_list=attrs["user2"]).exists()):
            raise ValidationError("You blocked this user.")
        elif not (UserRelationDetail.objects.filter(user=self.context['request'].user.id,
                                                    follower_list=attrs["user2"]).exists()):
            raise ValidationError("This user is not following you.")

        return attrs

    def save(self, validated_data):
        id = validated_data.pop('user2')
        user2 = User.objects.get(id=id)

        instance = UserRelationDetail.objects.all()

        UserRelationDetail.objects.filter(
            user=self.context['request'].user,
            follower_list=user2,
        ).delete()

        UserRelationDetail.objects.filter(
            user=user2,
            following_list=self.context['request'].user,
        ).delete()

        return instance


class UserBlockSerializer(serializers.ModelSerializer):
    user2 = serializers.IntegerField(allow_null=False)

    class Meta:
        model = UserRelationDetail
        fields = ['user', 'user2']
        read_only_fields = ("user",)

    def validate(self, attrs):
        if (attrs["user2"] == self.context['request'].user):
            raise ValidationError("You can not block yourself.")
        elif (UserRelationDetail.objects.filter(user=attrs["user2"] ,block_list=self.context['request'].user.id).exists()):
            raise ValidationError("You have been blocked by this user/ this user is not exist.")
        elif UserRelationDetail.objects.filter(user=self.context['request'].user.id, block_list=attrs["user2"]).exists():
            raise ValidationError("You already blocked this user.")

        return attrs

    def save(self, validated_data):
        id = validated_data.pop('user2')
        user2 = User.objects.get(id=id)

        instance = UserRelationDetail.objects.create(
            user=self.context['request'].user,
            block_list=user2,
        )

        return instance


class UserUnblockSerializer(serializers.ModelSerializer):
    user2 = serializers.IntegerField(allow_null=False)
    class Meta:
        model = UserRelationDetail
        fields = ['user', 'user2']
        read_only_fields = ("user",)

    def validate(self, attrs):
        if (attrs["user2"] == self.context['request'].user):
            raise ValidationError("You can not block yourself.")
        elif (UserRelationDetail.objects.filter(user=attrs["user2"] ,block_list=self.context['request'].user.id).exists()):
            raise ValidationError("You have been blocked by this user/ this user is not exist.")
        elif not (UserRelationDetail.objects.filter(user=self.context['request'].user.id,
                                               block_list=attrs["user2"]).exists()):
            raise ValidationError("This user is not in blocked list.")

        return attrs

    def save(self, validated_data):
        id = validated_data.pop('user2')
        user2 = User.objects.get(id=id)

        UserRelationDetail.objects.filter(
            user=self.context['request'].user,
            block_list=user2,
        ).delete()

        instance = UserRelationDetail.objects.all()

        return instance


class UserRequestAcceptSerializer(serializers.ModelSerializer):
    user2 = serializers.IntegerField(allow_null=False)

    class Meta:
        model = UserRelationDetail
        fields = ['user', 'user2']
        read_only_fields = ("user",)

    def validate(self, attrs):
        if (attrs["user2"] == self.context['request'].user):
            raise ValidationError("You can not accept request for yourself.")
        elif (UserRelationDetail.objects.filter(user=attrs["user2"] ,block_list=self.context['request'].user.id).exists()):
            raise ValidationError("You have been blocked by this user/ this user is not exist.")
        elif (UserRelationDetail.objects.filter(user=self.context['request'].user.id ,block_list=attrs["user2"]).exists()):
            raise ValidationError("You blocked this user.")
        elif not (UserRelationDetail.objects.filter(user=self.context['request'].user.id ,req_rx=attrs["user2"]).exists()):
            raise ValidationError("You did not receive request from this user.")

        return attrs

    def save(self, validated_data):
        id = validated_data.pop('user2')
        user2 = User.objects.get(id=id)

        instance = UserRelationDetail.objects.create(
            user=self.context['request'].user,
            follower_list=user2,
        )
        UserRelationDetail.objects.filter(
            user=self.context['request'].user,
            req_rx=user2,
        ).delete()

        UserRelationDetail.objects.create(
            user=user2,
            following_list=self.context['request'].user,
        )
        UserRelationDetail.objects.filter(
            user=user2,
            req_sent=self.context['request'].user,
        ).delete()

        return instance


class UserRequestDenySerializer(serializers.ModelSerializer):
    user2 = serializers.IntegerField(allow_null=False)

    class Meta:
        model = UserRelationDetail
        fields = ['user', 'user2']
        read_only_fields = ("user",)

    def validate(self, attrs):
        if (attrs["user2"] == self.context['request'].user):
            raise ValidationError("You can not accept request for yourself.")
        elif (UserRelationDetail.objects.filter(user=attrs["user2"] ,block_list=self.context['request'].user.id).exists()):
            raise ValidationError("You have been blocked by this user/ this user is not exist.")
        elif (UserRelationDetail.objects.filter(user=self.context['request'].user.id ,block_list=attrs["user2"]).exists()):
            raise ValidationError("You blocked this user.")
        elif not (UserRelationDetail.objects.filter(user=self.context['request'].user.id ,req_rx=attrs["user2"]).exists()):
            raise ValidationError("You did not receive request from this user.")

        return attrs

    def save(self, validated_data):
        id = validated_data.pop('user2')
        user2 = User.objects.get(id=id)

        UserRelationDetail.objects.filter(
            user=self.context['request'].user,
            req_rx=user2,
        ).delete()

        UserRelationDetail.objects.filter(
            user=user2,
            req_sent=self.context['request'].user,
        ).delete()

        instance = UserRelationDetail.objects.all()

        return instance


class MywallSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")

    comment_list = serializers.SerializerMethodField()

    def get_comment_list(self, obj):
        comment_list = []
        for comment in Comment.objects.filter(status=obj.id):
            comment_list.append(
                {
                    'id': comment.id,
                    # 'status': comment.status.id,
                    # 'base_comment': comment.base_comment,
                    # 'user': comment.user.id,
                    # 'comment_photo': comment.comment_photo,
                    # 'comment_text': comment.comment_text,
                    'like': comment.like,
                    'dislike': comment.dislike,
                    'comments_on_comment': comment.comments_on_comment,
                }
            )
        print(comment_list)
        return comment_list

    class Meta:
        model = Status
        fields = ["id", "user", "status_photo", "status_text", "like", "dislike", "comments", "url", "comment_list"]

        extra_kwargs = {
            "url": {"view_name": "api:mywall-detail", "lookup_field": "id"}
        }




