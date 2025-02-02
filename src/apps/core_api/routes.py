from rest_framework.routers import DefaultRouter

from .apis import MessageViewSet, ChatViewSet, ThreadViewSet

router = DefaultRouter()
router.register(r"messages", MessageViewSet)
router.register(r"chat", ChatViewSet, basename="chat")
router.register(r"threads", ThreadViewSet, basename="threads")

urlpatterns = router.urls
