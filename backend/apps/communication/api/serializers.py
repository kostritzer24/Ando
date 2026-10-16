from rest_framework import serializers

from apps.catalog.models import ConductRuleArticle, Section
from apps.students.models import Enrollment, Student

from ..models import Announcement, ConductReport, Message


class AnnouncementSerializer(serializers.ModelSerializer):
    target_section = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Section.objects.all(), required=False, allow_null=True
    )
    published_by = serializers.CharField(source="published_by.username", read_only=True)

    class Meta:
        model = Announcement
        fields = [
            "public_id",
            "title",
            "content",
            "audience",
            "target_section",
            "published_at",
            "expires_at",
            "published_by",
            "is_active",
        ]
        read_only_fields = ["public_id", "published_at", "published_by"]


class ConductReportSerializer(serializers.ModelSerializer):
    """RF-24/RF-35. `articles` es de solo lectura (los nombres de los
    artículos marcados); para elegirlos al crear se manda `article_ids`,
    ver `ConductReportCreateSerializer`."""

    enrollment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Enrollment.objects.all()
    )
    guide_teacher = serializers.CharField(source="guide_teacher.username", read_only=True)
    direction_member = serializers.CharField(
        source="direction_member.username", read_only=True, default=None
    )
    articles = serializers.SlugRelatedField(slug_field="description", many=True, read_only=True)

    class Meta:
        model = ConductReport
        fields = [
            "public_id",
            "enrollment",
            "report_date",
            "severity",
            "incident_description",
            "immediate_actions",
            "other_violation_detail",
            "sanction_type",
            "sanction_detail",
            "commitments",
            "guide_teacher",
            "direction_member",
            "articles",
            "status",
            "published_at",
            "is_active",
        ]
        read_only_fields = [
            "public_id",
            "guide_teacher",
            "direction_member",
            "status",
            "published_at",
        ]


class ConductReportCreateSerializer(serializers.Serializer):
    enrollment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Enrollment.objects.all()
    )
    report_date = serializers.DateField()
    severity = serializers.ChoiceField(choices=ConductReport.GRAVEDADES)
    incident_description = serializers.CharField()
    immediate_actions = serializers.CharField()
    other_violation_detail = serializers.CharField(required=False, allow_blank=True, default="")
    sanction_type = serializers.ChoiceField(choices=ConductReport.SANCIONES)
    sanction_detail = serializers.CharField(required=False, allow_blank=True, default="")
    commitments = serializers.CharField()
    article_ids = serializers.SlugRelatedField(
        slug_field="public_id",
        queryset=ConductRuleArticle.objects.all(),
        many=True,
        required=False,
        default=list,
    )


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source="sender.username", read_only=True)
    sender_name = serializers.SerializerMethodField()
    sender_label = serializers.SerializerMethodField()
    sender_role = serializers.CharField(source="sender.role.name", read_only=True)
    section = serializers.SlugRelatedField(slug_field="public_id", queryset=Section.objects.all())
    original_message = serializers.SlugRelatedField(slug_field="public_id", read_only=True)

    class Meta:
        model = Message
        fields = [
            "public_id",
            "sender",
            "sender_name",
            "sender_label",
            "sender_role",
            "section",
            "subject",
            "content",
            "original_message",
            "status",
            "created_at",
            "is_active",
        ]
        read_only_fields = ["public_id", "sender", "original_message", "status", "created_at"]

    def get_sender_name(self, mensaje) -> str:
        return mensaje.sender.nombre_completo()

    def get_sender_label(self, mensaje) -> str:
        """Cómo se reconoce a quien escribe en el lado administrativo: una
        familia aparece como "Usuario familia - <estudiante(s)>" (los de esa
        sección vinculados a la cuenta), el resto por su nombre."""
        if mensaje.sender.role.name != "Padre de familia":
            return mensaje.sender.nombre_completo()
        cache = self.context.setdefault("_etiquetas_familia", {})
        clave = (mensaje.sender_id, mensaje.section_id)
        if clave not in cache:
            estudiantes = Student.objects.filter(
                guardian_links__guardian__user_id=mensaje.sender_id,
                guardian_links__is_active=True,
                enrollments__section_id=mensaje.section_id,
                enrollments__is_active=True,
            ).distinct()
            nombres = ", ".join(e.nombre_completo() for e in estudiantes)
            cache[clave] = f"Usuario familia - {nombres}" if nombres else "Usuario familia"
        return cache[clave]


class MessageReplySerializer(serializers.Serializer):
    content = serializers.CharField()
