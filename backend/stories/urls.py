from rest_framework.routers import DefaultRouter

from .views import InstagramAccountViewSet, StoryPostViewSet

router = DefaultRouter()
router.register("cuentas", InstagramAccountViewSet, basename="cuenta")
router.register("historias", StoryPostViewSet, basename="historia")

urlpatterns = router.urls
