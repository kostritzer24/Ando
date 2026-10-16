from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("attendance", views.AttendanceViewSet, basename="attendance")
router.register("justifications", views.JustificationViewSet, basename="justification")

urlpatterns = [
    *router.urls,
]
