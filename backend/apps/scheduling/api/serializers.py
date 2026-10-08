from rest_framework import serializers

from apps.accounts.models import User
from apps.catalog.models import Course, SchoolCycle, Section

from ..models import CalendarEvent, ScheduleBlock, TeacherAssignment


class TeacherAssignmentSerializer(serializers.ModelSerializer):
    teacher = serializers.SlugRelatedField(slug_field="public_id", queryset=User.objects.all())
    course = serializers.SlugRelatedField(slug_field="public_id", queryset=Course.objects.all())
    section = serializers.SlugRelatedField(slug_field="public_id", queryset=Section.objects.all())
    cycle = serializers.SlugRelatedField(slug_field="public_id", queryset=SchoolCycle.objects.all())
    # `/sections/` y `/courses/` viven detrás del área "datos_maestros"
    # (docs/permisos-roles.md: DOC/GUÍA/TALL no tienen acceso), pero un
    # docente sí necesita saber el grado/letra de su propia sección y el
    # nombre de su propio curso para las pantallas operativas (asistencia,
    # y más adelante notas) — se exponen acá, de solo lectura, en vez de
    # abrirle el catálogo completo.
    section_grade = serializers.CharField(source="section.grade", read_only=True)
    section_letter = serializers.CharField(source="section.letter", read_only=True)
    section_type = serializers.CharField(source="section.type", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    # Quien consulta asignaciones (p. ej. Coordinación) no tiene acceso a
    # `/users/`, pero necesita ver el nombre de la persona asignada.
    teacher_name = serializers.SerializerMethodField()

    def get_teacher_name(self, obj) -> str:
        return obj.teacher.nombre_completo()

    class Meta:
        model = TeacherAssignment
        fields = [
            "public_id",
            "teacher",
            "teacher_name",
            "course",
            "course_name",
            "section",
            "section_grade",
            "section_letter",
            "section_type",
            "cycle",
            "is_active",
        ]
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
