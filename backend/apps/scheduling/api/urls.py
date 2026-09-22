from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("assignments", views.TeacherAssignmentViewSet, basename="assignment")
router.register("schedule-blocks", views.ScheduleBlockViewSet, basename="schedule-block")
router.register("calendar-events", views.CalendarEventViewSet, basename="calendar-event")

urlpatterns = [
    path("schedule/mine/", views.MyScheduleView.as_view(), name="schedule-mine"),
    *router.urls,
]
