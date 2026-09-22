from rest_framework import serializers

from apps.accounts.models import User
from apps.catalog.models import Course, SchoolCycle, Section

from ..models import CalendarEvent, ScheduleBlock, TeacherAssignment


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    teacher = serializers.SlugRelatedField(slug_field="public_id", queryset=User.objects.all())
    course = serializers.SlugRelatedField(slug_field="public_id", queryset=Course.objects.all())
    section = serializers.SlugRelatedField(slug_field="public_id", queryset=Section.objects.all())
    cycle = serializers.SlugRelatedField(slug_field="public_id", queryset=SchoolCycle.objects.all())

    class Meta:
        model = TeacherAssignment
        fields = ["public_id", "teacher", "course", "section", "cycle", "is_active"]
        read_only_fields = ["public_id"]


class ScheduleBlockSerializer(serializers.ModelSerializer):
    assignment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=TeacherAssignment.objects.all()
    )

    class Meta:
        model = ScheduleBlock
        fields = ["public_id", "assignment", "day_of_week", "period_number", "is_active"]
        read_only_fields = ["public_id"]


class CalendarEventSerializer(serializers.ModelSerializer):
    section = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Section.objects.all(), required=False, allow_null=True
    )
    assignment = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=TeacherAssignment.objects.all(),
        required=False,
        allow_null=True,
    )
    published_by = serializers.CharField(source="published_by.username", read_only=True)

    class Meta:
        model = CalendarEvent
        fields = [
            "public_id",
            "title",
            "type",
            "event_date",
            "start_time",
            "end_time",
            "section",
            "assignment",
            "materials",
            "published_by",
            "is_active",
        ]
        read_only_fields = ["public_id", "published_by"]
