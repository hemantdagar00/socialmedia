from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter

from socialmedia.users.api.views import UserViewSet
from socialmedia.newsfeed.api.views import StatusViewSet

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("users", UserViewSet, basename="user")
router.register("status", StatusViewSet, basename="status")
# router.register("votes", VotesViewSet, basename="votes")




app_name = "api"
urlpatterns = router.urls
