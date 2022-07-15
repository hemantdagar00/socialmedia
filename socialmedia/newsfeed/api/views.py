from attr import attrs
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.exceptions import NotFound
from .serializers import StatusCreateSerializer, StatusDetailSerializer, StatusUpdateSerializer, StatusVotesUpdateSerializer, \
    CommentDetailSerializer, CommentCreateSerializer, CommentUpdateSerializer, CommentVotesUpdateSerializer
from socialmedia.newsfeed.models import Status, Comment
from rest_framework.exceptions import ValidationError

User = get_user_model()


class StatusViewSet(RetrieveModelMixin,
                  ListModelMixin,
                  UpdateModelMixin,
                  DestroyModelMixin,
                  CreateModelMixin,
                  GenericViewSet):
    queryset = Status.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StatusCreateSerializer
        elif (
            hasattr(self, "action_map")
            and self.action_map.get("put", "") == "vote"
        ):
            return StatusVotesUpdateSerializer
        elif self.request.method == 'PUT':
            return StatusUpdateSerializer
        else:
            return StatusDetailSerializer

    @action(detail=False)
    def me(self, request):
        serializer = StatusDetailSerializer(request.status, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(serializer.validated_data)
        response_serializer = StatusDetailSerializer(obj, context={'request': request})
        return Response({"response": response_serializer.data, "status": "success"}, status=status.HTTP_201_CREATED)

    def get_queryset(self, *args, **kwargs):  # used in get_object
        return self.queryset.all()

    def get_object(self, *args, **kwargs):  # used in update
        self.queryset = self.get_queryset()
        obj = self.queryset.filter(id=self.kwargs['id']).first()
        if not obj:
            raise NotFound("Status not found.")
        return obj

    def update(self, request, *args, **kwargs):
        data_to_change = {'status_text': request.data.get("status_text")}
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=data_to_change, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"response": serializer.data, "status": "success"}, status=status.HTTP_202_ACCEPTED)


    def destroy(self, request, *args, **kwargs):
        if Status.objects.get(id=kwargs["id"]).user != self.request.user:
            raise ValidationError("You are not allowed to delete the status of other user")
        status_obj = get_object_or_404(Status, id=kwargs["id"])
        status_obj.delete()
        return Response(data={"status":"success"}, status=status.HTTP_204_NO_CONTENT)

    @action(methods=["PUT"], detail=True)
    def vote(self, request, *args, **kwargs):
        data_to_change = {
            'up_vote': request.data.get("up_vote"),
            'down_vote': request.data.get("down_vote"),
        }
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=data_to_change, partial=True) # data = request.data
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"response": serializer.data, "status": "success"}, status=status.HTTP_202_ACCEPTED)


class CommentViewSet(RetrieveModelMixin,
                  ListModelMixin,
                  UpdateModelMixin,
                  DestroyModelMixin,
                  CreateModelMixin,
                  GenericViewSet):
    queryset = Comment.objects.all()
    lookup_field = "id"

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        elif (
            hasattr(self, "action_map")
            and self.action_map.get("put", "") == "vote"
        ):
            return CommentVotesUpdateSerializer
        elif self.request.method == 'PUT':
            return CommentUpdateSerializer
        else:
            return CommentDetailSerializer

    @action(detail=False)
    def me(self, request):
        serializer = CommentDetailSerializer(request.status, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # increament comments number
        if (serializer.data.serializer["status"].value != None) and (serializer.data.serializer["base_comment"].value == None):
            comments = Status.objects.get(id=serializer.data.serializer["status"].value).comments
            Status.objects.filter(id=serializer.data.serializer["status"].value).update(comments=comments+1)
        elif (serializer.data.serializer["status"].value == None) and (serializer.data.serializer["base_comment"].value != None):
            comment_track = Comment.objects.get(id=serializer.data.serializer['base_comment'].value).id
            status_track=Comment.objects.get(id=comment_track).status.id
            comments = Status.objects.get(id=status_track).comments
            Status.objects.filter(id=status_track).update(comments=comments + 1)
            comments_on_comment = Comment.objects.get(id=serializer.data.serializer["base_comment"].value).comments_on_comment
            Comment.objects.filter(id=serializer.data.serializer["base_comment"].value).update(comments_on_comment=comments_on_comment + 1)

        obj = serializer.save(serializer.validated_data)
        response_serializer = CommentDetailSerializer(obj, context={'request': request})
        return Response({"response": response_serializer.data, "status": "success"}, status=status.HTTP_201_CREATED)

    def get_queryset(self, *args, **kwargs):  # used in get_object
        return self.queryset.all()

    def get_object(self, *args, **kwargs):  # used in update
        self.queryset = self.get_queryset()
        obj = self.queryset.filter(id=self.kwargs['id']).first()
        if not obj:
            raise NotFound("Comment not found.")
        return obj

    def update(self, request, *args, **kwargs):
        data_to_change = {'comment_text': request.data.get("comment_text")}
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=data_to_change, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"response": serializer.data, "status": "success"}, status=status.HTTP_202_ACCEPTED)


    def destroy(self, request, *args, **kwargs):

        if (Comment.objects.get(id=kwargs["id"]).user != self.request.user) and \
            (Status.objects.get(id=Comment.objects.get(id=kwargs['id']).status.id).user != self.request.user) and \
            (Comment.objects.get(id=Comment.objects.get(id=kwargs['id']).base_comment.id).user != self.request.user):

            raise ValidationError("You are not allowed to delete this comment.")

        comment_obj = get_object_or_404(Comment, id=kwargs["id"])

        # decrement comments number
        statusinstance = Comment.objects.get(id=comment_obj.id).status
        commentinstance = Comment.objects.get(id=comment_obj.id).base_comment



        comments_on_comment = Comment.objects.get(id=commentinstance.id).comments_on_comment
        Comment.objects.filter(id=commentinstance.id).update(comments_on_comment=comments_on_comment-1)

        comment_obj.delete()

        comments = Status.objects.filter(comment__status=statusinstance).count()
        Status.objects.filter(id=statusinstance.id).update(comments=comments)

        return Response(data={"status":"success"}, status=status.HTTP_204_NO_CONTENT)


    @action(methods=["PUT"], detail=True)
    def vote(self, request, *args, **kwargs):
        data_to_change = {
            'up_vote': request.data.get("up_vote"),
            'down_vote': request.data.get("down_vote"),
        }
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=data_to_change, partial=True) # data = request.data
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"response": serializer.data, "status": "success"}, status=status.HTTP_202_ACCEPTED)










