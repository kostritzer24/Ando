from rest_framework import serializers

from apps.catalog.models import ActivityType, GradingUnit, Section
from apps.scheduling.models import TeacherAssignment
from apps.students.models import Enrollment

from ..models import Activity, Grade, GradeChangeRequest, ReportCard


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
        # La baja es DELETE (baja lógica, validada en el servicio), no un
        # PATCH de is_active que saltaría esas validaciones.
        read_only_fields = ["public_id", "is_active"]


class ActivityUpdateSerializer(serializers.ModelSerializer):
    """Editar una actividad: solo nombre, tipo, punteo máximo y fecha. La
    asignación y la unidad no se mueven."""

    activity_type = serializers.SlugRelatedField(
        slug_field="public_id", queryset=ActivityType.objects.all()
    )

    class Meta:
        model = Activity
        fields = ["activity_type", "name", "max_score", "due_date"]


class GradeSerializer(serializers.ModelSerializer):
    """RN-06: nunca expone `raw_score` — solo `current_score`, la nota
    vigente que entra en los promedios y la única que ve la familia.

    Los campos denormalizados (`course_name`, `unit_number`,
    `activity_name`, `max_score`) siguen el mismo criterio que
    `TeacherAssignmentSerializer` (sección "scheduling" del contrato): la
    familia no llega a `/activities/` ni a `/assignments/` (RF-29 la
    necesita agrupada por curso y unidad), así que se exponen acá en vez
    de abrirle esos dos catálogos completos."""

    enrollment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Enrollment.objects.all()
    )
    activity = serializers.SlugRelatedField(slug_field="public_id", queryset=Activity.objects.all())
    recorded_by = serializers.CharField(source="recorded_by.username", read_only=True)
    course_name = serializers.CharField(source="activity.assignment.course.name", read_only=True)
    unit_number = serializers.IntegerField(source="activity.unit.number", read_only=True)
    activity_name = serializers.CharField(source="activity.name", read_only=True)
    max_score = serializers.DecimalField(
        source="activity.max_score", max_digits=5, decimal_places=2, read_only=True
    )

    class Meta:
        model = Grade
        fields = [
            "public_id",
            "enrollment",
            "activity",
            "current_score",
            "source",
            "recorded_by",
            "course_name",
            "unit_number",
            "activity_name",
            "max_score",
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


class ReportCardSerializer(serializers.ModelSerializer):
    enrollment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Enrollment.objects.all()
    )
    unit = serializers.SlugRelatedField(slug_field="public_id", queryset=GradingUnit.objects.all())
    generated_by = serializers.CharField(source="generated_by.username", read_only=True)
    approved_by = serializers.CharField(source="approved_by.username", read_only=True, default=None)

    class Meta:
        model = ReportCard
        fields = [
            "public_id",
            "enrollment",
            "unit",
            "status",
            "generated_by",
            "approved_by",
            "approved_at",
            "published_at",
        ]
        read_only_fields = [
            "public_id",
            "status",
            "generated_by",
            "approved_by",
            "approved_at",
            "published_at",
        ]


class ReportCardGenerateSerializer(serializers.Serializer):
    section = serializers.SlugRelatedField(slug_field="public_id", queryset=Section.objects.all())
    unit = serializers.SlugRelatedField(slug_field="public_id", queryset=GradingUnit.objects.all())
