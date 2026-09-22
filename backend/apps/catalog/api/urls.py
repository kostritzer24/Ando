from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("cycles", views.SchoolCycleViewSet, basename="cycle")
router.register("sections", views.SectionViewSet, basename="section")
router.register("courses", views.CourseViewSet, basename="course")
router.register("activity-types", views.ActivityTypeViewSet, basename="activity-type")
router.register(
    "justification-types", views.JustificationTypeViewSet, basename="justification-type"
)
router.register("document-types", views.DocumentTypeViewSet, basename="document-type")
router.register("scholarships", views.ScholarshipViewSet, basename="scholarship")
router.register(
    "conduct-rule-articles", views.ConductRuleArticleViewSet, basename="conduct-rule-article"
)

_grading_unit_list = views.GradingUnitViewSet.as_view({"get": "list", "post": "create"})
_grading_unit_detail = views.GradingUnitViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update", "put": "update", "delete": "destroy"}
)

urlpatterns = [
    path("cycles/<uuid:cycle_public_id>/units/", _grading_unit_list, name="grading-unit-list"),
    path(
        "cycles/<uuid:cycle_public_id>/units/<uuid:public_id>/",
        _grading_unit_detail,
        name="grading-unit-detail",
    ),
    *router.urls,
]
