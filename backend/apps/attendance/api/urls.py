from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("attendance", views.AttendanceViewSet, basename="attendance")
router.register("justifications", views.JustificationViewSet, basename="justification")

urlpatterns = [
    path(
        "attendance/template/<uuid:section_public_id>/<str:fecha>/",
        views.AttendanceTemplateDownloadView.as_view(),
        name="attendance-template-download",
    ),
    path(
        "attendance/template/upload/",
        views.AttendanceTemplateUploadView.as_view(),
        name="attendance-template-upload",
    ),
    *router.urls,
]
