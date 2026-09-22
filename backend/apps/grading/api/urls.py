from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("activities", views.ActivityViewSet, basename="activity")
router.register("grades", views.GradeViewSet, basename="grade")
router.register(
    "grade-change-requests", views.GradeChangeRequestViewSet, basename="grade-change-request"
)
router.register("report-cards", views.ReportCardViewSet, basename="report-card")

urlpatterns = [
    path(
        "grades/template/<uuid:assignment_public_id>/<uuid:unit_public_id>/",
        views.GradeTemplateDownloadView.as_view(),
        name="grade-template-download",
    ),
    path(
        "grades/template/preview/",
        views.GradeTemplatePreviewView.as_view(),
        name="grade-template-preview",
    ),
    path(
        "grades/template/upload/",
        views.GradeTemplateUploadView.as_view(),
        name="grade-template-upload",
    ),
    *router.urls,
]
