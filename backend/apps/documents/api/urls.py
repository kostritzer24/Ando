from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("documents", views.IssuedDocumentViewSet, basename="issued-document")

urlpatterns = [
    path("documents/issue/", views.DocumentIssueView.as_view(), name="document-issue"),
    path(
        "verify/<str:verification_code>/",
        views.VerifyDocumentView.as_view(),
        name="verify-document",
    ),
    *router.urls,
]
