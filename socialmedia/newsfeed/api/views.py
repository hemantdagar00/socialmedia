from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.exceptions import NotFound
from .serializers import StatusCreateSerializer, StatusDetailSerializer, StatusUpdateSerializer, VotesUpdateSerializer
from socialmedia.newsfeed.models import Status, VoteTracker
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
            return VotesUpdateSerializer
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
















