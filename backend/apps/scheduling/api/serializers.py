from rest_framework import serializers

from apps.accounts.models import User
from apps.catalog.models import Course, SchoolCycle, Section

from ..models import TeacherAssignment


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    teacher = serializers.SlugRelatedField(slug_field="public_id", queryset=User.objects.all())
    course = serializers.SlugRelatedField(slug_field="public_id", queryset=Course.objects.all())
    section = serializers.SlugRelatedField(slug_field="public_id", queryset=Section.objects.all())
    cycle = serializers.SlugRelatedField(slug_field="public_id", queryset=SchoolCycle.objects.all())

    class Meta:
        model = TeacherAssignment
        fields = ["public_id", "teacher", "course", "section", "cycle", "is_active"]
        read_only_fields = ["public_id"]
