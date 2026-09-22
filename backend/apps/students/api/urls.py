from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("students", views.StudentViewSet, basename="student")
router.register("guardians", views.GuardianViewSet, basename="guardian")
router.register("enrollments", views.EnrollmentViewSet, basename="enrollment")

urlpatterns = router.urls
