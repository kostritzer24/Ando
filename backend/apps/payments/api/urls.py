from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("payments", views.PaymentViewSet, basename="payment")

urlpatterns = [
    path(
        "solvency/<uuid:enrollment_public_id>/",
        views.SolvencyView.as_view(),
        name="solvency-detail",
    ),
    path(
        "solvency/<uuid:enrollment_public_id>/certificate/",
        views.SolvencyCertificateView.as_view(),
        name="solvency-certificate",
    ),
    *router.urls,
]
