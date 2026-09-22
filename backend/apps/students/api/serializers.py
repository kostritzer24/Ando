from rest_framework import serializers

from apps.accounts.models import User
from apps.catalog.models import Scholarship, SchoolCycle, Section

from ..models import Enrollment, Guardian, GuardianStudentLink, Student


class StudentSerializer(serializers.ModelSerializer):
    """Serializer general: nunca incluye `health_notes` ni
    `socioeconomic_notes` (RNF-04) — esos solo viven en
    `StudentSensitiveSerializer`, detrás de su propio permiso."""

    class Meta:
        model = Student
        fields = [
            "public_id",
            "internal_code",
            "first_name",
            "last_name",
            "birth_date",
            "address",
            "previous_institution",
            "is_active",
        ]
        read_only_fields = ["public_id", "internal_code"]


class StudentCreateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    birth_date = serializers.DateField()
    address = serializers.CharField(required=False, allow_blank=True, default="")
    previous_institution = serializers.CharField(required=False, allow_blank=True, default="")


class StudentSensitiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ["public_id", "health_notes", "socioeconomic_notes"]
        read_only_fields = ["public_id"]


class GuardianSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="public_id", queryset=User.objects.all())

    class Meta:
        model = Guardian
        fields = [
            "public_id",
            "user",
            "full_name",
            "phone",
            "messaging_number",
            "occupation",
            "is_active",
        ]
        read_only_fields = ["public_id"]


class GuardianStudentLinkSerializer(serializers.Serializer):
    student = serializers.SlugRelatedField(slug_field="public_id", queryset=Student.objects.all())
    relationship = serializers.CharField(max_length=60)
    is_primary = serializers.BooleanField(required=False, default=False)


class GuardianStudentLinkReadSerializer(serializers.ModelSerializer):
    """GET /guardians/{id}/link-student/ — para mostrar los vínculos ya
    existentes de un encargado (la escritura usa el serializer de
    arriba, más angosto a propósito: solo pide lo que hace falta para
    crear el vínculo, no lo que hace falta para mostrarlo)."""

    student_public_id = serializers.CharField(source="student.public_id", read_only=True)
    student_internal_code = serializers.CharField(source="student.internal_code", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = GuardianStudentLink
        fields = [
            "public_id",
            "student_public_id",
            "student_internal_code",
            "student_name",
            "relationship",
            "is_primary",
        ]

    def get_student_name(self, obj: GuardianStudentLink) -> str:
        return obj.student.nombre_completo()


class EnrollmentSerializer(serializers.ModelSerializer):
    student = serializers.SlugRelatedField(slug_field="public_id", queryset=Student.objects.all())
    section = serializers.SlugRelatedField(slug_field="public_id", queryset=Section.objects.all())
    cycle = serializers.SlugRelatedField(slug_field="public_id", queryset=SchoolCycle.objects.all())
    scholarship = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=Scholarship.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Enrollment
        fields = [
            "public_id",
            "student",
            "section",
            "cycle",
            "scholarship",
            "status",
            "enrolled_at",
            "is_active",
        ]
        # "status" no se acepta del cliente en esta fase: toda inscripción
        # nueva empieza "activo" (default del modelo); los cambios de
        # estado (retiro, graduación, traslado) no están en el alcance de
        # RF-03 todavía.
        read_only_fields = ["public_id", "status"]
