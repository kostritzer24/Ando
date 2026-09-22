from rest_framework import serializers

from apps.catalog.models import ActivityType, GradingUnit
from apps.scheduling.models import TeacherAssignment
from apps.students.models import Enrollment

from ..models import Activity, Grade, GradeChangeRequest


class ActivitySerializer(serializers.ModelSerializer):
    assignment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=TeacherAssignment.objects.all()
    )
    unit = serializers.SlugRelatedField(slug_field="public_id", queryset=GradingUnit.objects.all())
    activity_type = serializers.SlugRelatedField(
        slug_field="public_id", queryset=ActivityType.objects.all()
    )

    class Meta:
        model = Activity
        fields = [
            "public_id",
            "assignment",
            "unit",
            "activity_type",
            "name",
            "max_score",
            "due_date",
            "is_active",
        ]
        read_only_fields = ["public_id"]


class GradeSerializer(serializers.ModelSerializer):
    """RN-06: nunca expone `raw_score` — solo `current_score`, la nota
    vigente que entra en los promedios y la única que ve la familia."""

    enrollment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Enrollment.objects.all()
    )
    activity = serializers.SlugRelatedField(slug_field="public_id", queryset=Activity.objects.all())
    recorded_by = serializers.CharField(source="recorded_by.username", read_only=True)

    class Meta:
        model = Grade
        fields = [
            "public_id",
            "enrollment",
            "activity",
            "current_score",
            "source",
            "recorded_by",
            "is_active",
        ]
        read_only_fields = ["public_id", "current_score", "source", "recorded_by"]


class GradeCreateSerializer(serializers.Serializer):
    enrollment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Enrollment.objects.all()
    )
    activity = serializers.SlugRelatedField(slug_field="public_id", queryset=Activity.objects.all())
    raw_score = serializers.DecimalField(max_digits=5, decimal_places=2)


class GradeChangeRequestSerializer(serializers.ModelSerializer):
    grade = serializers.SlugRelatedField(slug_field="public_id", queryset=Grade.objects.all())
    requested_by = serializers.CharField(source="requested_by.username", read_only=True)
    authorized_by = serializers.CharField(
        source="authorized_by.username", read_only=True, default=None
    )

    class Meta:
        model = GradeChangeRequest
        fields = [
            "public_id",
            "grade",
            "original_score",
            "requested_score",
            "reason",
            "requested_by",
            "status",
            "authorized_by",
            "decided_at",
        ]
        read_only_fields = [
            "public_id",
            "original_score",
            "requested_by",
            "status",
            "authorized_by",
            "decided_at",
        ]
