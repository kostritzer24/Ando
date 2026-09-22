from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("assignments", views.TeacherAssignmentViewSet, basename="assignment")

urlpatterns = router.urls
