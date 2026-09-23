from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("announcements", views.AnnouncementViewSet, basename="announcement")
router.register("conduct-reports", views.ConductReportViewSet, basename="conduct-report")
router.register("messages", views.MessageViewSet, basename="message")

urlpatterns = router.urls
