from rest_framework import serializers

from apps.accounts.models import User

from ..models import (
    ActivityType,
    ConductRuleArticle,
    Course,
    DocumentType,
    GradingUnit,
    JustificationType,
    Scholarship,
    SchoolCycle,
    Section,
)


class SchoolCycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolCycle
        fields = ["public_id", "year", "start_date", "end_date", "status", "is_active"]
        read_only_fields = ["public_id"]


class GradingUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradingUnit
        fields = [
            "public_id",
            "number",
            "start_date",
            "end_date",
            "grades_due_date",
            "report_card_enabled_date",
            "is_active",
        ]
        # Las fechas derivadas nunca se reciben del cliente (RN-10): las
        # calcula catalog/services/grading_unit.py a partir de end_date.
        read_only_fields = ["public_id", "grades_due_date", "report_card_enabled_date"]


class SectionSerializer(serializers.ModelSerializer):
    cycle = serializers.SlugRelatedField(slug_field="public_id", queryset=SchoolCycle.objects.all())
    cycle_year = serializers.IntegerField(source="cycle.year", read_only=True)
    homeroom_teacher = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Section
        fields = [
            "public_id",
            "cycle",
            "cycle_year",
            "grade",
            "letter",
            "type",
            "homeroom_teacher",
            "is_active",
        ]
        read_only_fields = ["public_id"]

    def validate(self, attrs):
        # Una misma sección (ciclo + grado + letra + tipo) no se repite:
        # sin esto se podían crear «Quinto Bachillerato A» sin límite.
        ciclo = attrs.get("cycle", getattr(self.instance, "cycle", None))
        grado = (attrs.get("grade", getattr(self.instance, "grade", "")) or "").strip()
        letra = (attrs.get("letter", getattr(self.instance, "letter", "")) or "").strip()
        tipo = attrs.get("type", getattr(self.instance, "type", None))
        repetidas = Section.objects.filter(
            cycle=ciclo, grade__iexact=grado, letter__iexact=letra, type=tipo, is_active=True
        )
        if self.instance is not None:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError(
                "Ya existe esa sección en el ciclo. Cambia el grado o la letra."
            )
        attrs["grade"] = grado
        attrs["letter"] = letra
        return attrs


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["public_id", "name", "type", "is_active"]
        read_only_fields = ["public_id"]

    def validate(self, attrs):
        nombre = attrs.get("name", getattr(self.instance, "name", None))
        tipo = attrs.get("type", getattr(self.instance, "type", None))
        repetidos = Course.objects.filter(
            name__iexact=(nombre or "").strip(), type=tipo, is_active=True
        )
        if self.instance is not None:
            repetidos = repetidos.exclude(pk=self.instance.pk)
        if repetidos.exists():
            raise serializers.ValidationError({"name": "Ya existe un curso con ese nombre y tipo."})
        return attrs


class ActivityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityType
        fields = ["public_id", "name", "counts_as_short_quiz", "is_active"]
        read_only_fields = ["public_id"]


class JustificationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = JustificationType
        fields = ["public_id", "name", "requires_document", "is_active"]
        read_only_fields = ["public_id"]


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = ["public_id", "name", "template_key", "is_active"]
        read_only_fields = ["public_id"]


class ScholarshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scholarship
        fields = ["public_id", "name", "description", "is_active"]
        read_only_fields = ["public_id"]


class ConductRuleArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConductRuleArticle
        fields = ["public_id", "chapter", "code", "description", "is_active"]
        read_only_fields = ["public_id"]
