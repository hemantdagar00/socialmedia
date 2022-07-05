from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, UpdateModelMixin, CreateModelMixin, DestroyModelMixin
from rest_framework.exceptions import NotFound
from .serializers import UserDetailSerializer, UserUpdateSerializer, UserCreateSerializer
from socialmedia.newsfeed.models import Status
User = get_user_model()


class UserViewSet(RetrieveModelMixin,
                  ListModelMixin,
                  UpdateModelMixin,
                  DestroyModelMixin,
                  CreateModelMixin,
                  GenericViewSet):
    queryset = User.objects.all()
    lookup_field = "username"

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        elif self.request.method == 'PUT':
            return UserUpdateSerializer
        else:
            return UserDetailSerializer

    @action(detail=False)
    def me(self, request):
        serializer = UserDetailSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)                           #, context={'request': request})
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(serializer.validated_data)
        response_serializer = UserDetailSerializer(obj, context={'request': request})
        return Response({"response": response_serializer.data, "status": "success"}, status=status.HTTP_201_CREATED)

    def get_queryset(self, *args, **kwargs):                                         # used in get_object
        return self.queryset.all()

    # def list(self, request, *args, **kwargs):

    def get_object(self, *args, **kwargs):                                           # used in update
        self.queryset = self.get_queryset()
        obj = self.queryset.filter(username=self.kwargs['username']).first()
        if not obj:
            raise NotFound("User not found.")
        return obj

    def update(self, request, *args, **kwargs):
        data_to_change = {'name': request.data.get("name")}
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=data_to_change, partial=True)
        if serializer.is_valid():
            self.perform_update(serializer)
        return Response({"response": serializer.data, "status": "success"}, status=status.HTTP_202_ACCEPTED)



