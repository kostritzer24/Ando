from django.utils import timezone
from rest_framework import serializers

from apps.catalog.models import JustificationType
from apps.core.validators import validar_documento_de_respaldo
from apps.students.models import Enrollment

from ..models import Attendance, Justification


class AttendanceSerializer(serializers.ModelSerializer):
    enrollment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Enrollment.objects.all()
    )
    recorded_by = serializers.CharField(source="recorded_by.username", read_only=True)
    # RF-31: la familia distingue jornada matutina de taller sin llegar a
    # `/sections/` (datos_maestros, fuera de su alcance) — mismo criterio
    # que los campos denormalizados de `GradeSerializer`.
    section_type = serializers.CharField(source="enrollment.section.type", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "public_id",
            "enrollment",
            "date",
            "status",
            "source",
            "recorded_by",
            "section_type",
            "is_active",
        ]
        read_only_fields = ["public_id", "source", "recorded_by"]


class AttendanceCreateSerializer(serializers.Serializer):
    enrollment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Enrollment.objects.all()
    )
    date = serializers.DateField()
    status = serializers.ChoiceField(choices=Attendance.ESTADOS)

    def validate_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError(
                "No se puede registrar asistencia de una fecha futura."
            )
        if value.weekday() >= 5:
            raise serializers.ValidationError(
                "El centro no abre sábados ni domingos: elige un día de lunes a viernes."
            )
        return value


class JustificationSerializer(serializers.ModelSerializer):
    attendance = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Attendance.objects.all()
    )
    justification_type = serializers.SlugRelatedField(
        slug_field="public_id", queryset=JustificationType.objects.all()
    )
    submitted_by = serializers.CharField(source="submitted_by.username", read_only=True)
    resolved_by = serializers.CharField(source="resolved_by.username", read_only=True, default=None)
    # Nunca se expone la URL directa del archivo (sección 14.2 del prompt
    # maestro: nada sensible se sirve desde una carpeta pública) — se
    # sube acá, pero se descarga por la acción autenticada
    # GET /justifications/{id}/document/.
    supporting_document = serializers.FileField(
        write_only=True, required=False, validators=[validar_documento_de_respaldo]
    )
    has_supporting_document = serializers.SerializerMethodField()

    class Meta:
        model = Justification
        fields = [
            "public_id",
            "attendance",
            "justification_type",
            "reason_detail",
            "supporting_document",
            "has_supporting_document",
            "resolution",
            "submitted_by",
            "resolved_by",
            "resolved_at",
        ]
        read_only_fields = ["public_id", "resolution", "submitted_by", "resolved_by", "resolved_at"]

    def get_has_supporting_document(self, obj) -> bool:
        return bool(obj.supporting_document)


class JustificationResolveSerializer(serializers.Serializer):
    aprobar = serializers.BooleanField()
