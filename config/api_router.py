from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from socialmedia.users.api.views import UserViewSet
from socialmedia.newsfeed.api.views import StatusViewSet, CommentViewSet,\
    UserRelationDetailViewSet, MywallDetailViewSet, NewsDetailViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet, basename="user")
router.register("status", StatusViewSet, basename="status")
router.register("comment", CommentViewSet, basename="comment")
router.register("userrelationdetail", UserRelationDetailViewSet, basename="userrelationdetail")
router.register("mywall", MywallDetailViewSet, basename="mywall")
router.register("news", NewsDetailViewSet, basename="news")





app_name = "api"
urlpatterns = router.urls
