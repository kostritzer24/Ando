from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.catalog.models import ConductRuleArticle, Section
from apps.students.models import Enrollment, Guardian, Student

from ..models import Announcement, ConductReport, Conversation, Message
from ..services.announcement import puede_administrar


class AnnouncementSerializer(serializers.ModelSerializer):
    target_section = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Section.objects.all(), required=False, allow_null=True
    )
    published_by = serializers.CharField(source="published_by.username", read_only=True)
    published_by_name = serializers.SerializerMethodField()
    puede_editar = serializers.SerializerMethodField()

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
            "published_by_name",
            "puede_editar",
            "is_active",
        ]
        read_only_fields = ["public_id", "published_at", "published_by"]

    def get_published_by_name(self, aviso) -> str:
        return aviso.published_by.nombre_completo()

    def get_puede_editar(self, aviso) -> bool:
        """RN-18: la interfaz solo ofrece editar o retirar lo que la API
        aceptaría; sin `request` (p. ej. al serializar fuera de una vista)
        no se ofrece nada."""
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        tiene_edicion = request.user.role.permissions.get("avisos") == "editar"
        return tiene_edicion and puede_administrar(aviso, request.user)


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


ROL_FAMILIA = "Padre de familia"


class MessageSerializer(serializers.ModelSerializer):
    """Un mensaje dice quién lo escribió (HU-25): nombre y rol; una familia
    aparece como "Encargado / Alumno"."""

    sender = serializers.CharField(source="sender.username", read_only=True)
    sender_name = serializers.SerializerMethodField()
    sender_label = serializers.SerializerMethodField()
    sender_role = serializers.CharField(source="sender.role.name", read_only=True)

    class Meta:
        model = Message
        fields = [
            "public_id",
            "sender",
            "sender_name",
            "sender_label",
            "sender_role",
            "content",
            "created_at",
        ]
        read_only_fields = fields

    def get_sender_name(self, mensaje) -> str:
        return mensaje.sender.nombre_completo()

    def get_sender_label(self, mensaje) -> str:
        conversacion = mensaje.conversation
        if mensaje.sender.role.name == ROL_FAMILIA and mensaje.sender_id == (
            conversacion.guardian.user_id
        ):
            return etiqueta_familia(conversacion)
        return mensaje.sender.nombre_completo()


def etiqueta_familia(conversacion) -> str:
    return f"{conversacion.guardian.full_name} / {conversacion.student.nombre_completo()}"


class ConversationSerializer(serializers.ModelSerializer):
    """RF-25/RF-37/RF-38. `no_leido` es de quien consulta (RN-19), nunca de
    los demás participantes."""

    student = serializers.SlugRelatedField(slug_field="public_id", read_only=True)
    guardian = serializers.SlugRelatedField(slug_field="public_id", read_only=True)
    section = serializers.SlugRelatedField(slug_field="public_id", read_only=True)
    student_name = serializers.CharField(source="student.nombre_completo", read_only=True)
    guardian_name = serializers.CharField(source="guardian.full_name", read_only=True)
    family_label = serializers.SerializerMethodField()
    section_label = serializers.CharField(source="section.__str__", read_only=True)
    created_by_name = serializers.CharField(source="created_by.nombre_completo", read_only=True)
    no_leido = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "public_id",
            "subject",
            "student",
            "student_name",
            "guardian",
            "guardian_name",
            "family_label",
            "section",
            "section_label",
            "created_by_name",
            "created_at",
            "last_message_at",
            "no_leido",
        ]
        read_only_fields = fields

    def get_family_label(self, conversacion) -> str:
        return etiqueta_familia(conversacion)

    def get_no_leido(self, conversacion) -> bool:
        return bool(getattr(conversacion, "no_leido", False))


class ConversationDetailSerializer(ConversationSerializer):
    messages = serializers.SerializerMethodField()

    class Meta(ConversationSerializer.Meta):
        fields = [*ConversationSerializer.Meta.fields, "messages"]
        read_only_fields = fields

    @extend_schema_field(MessageSerializer(many=True))
    def get_messages(self, conversacion):
        mensajes = conversacion.messages.filter(is_active=True).select_related(
            "sender__role", "conversation__guardian", "conversation__student"
        )
        return MessageSerializer(mensajes, many=True).data


class ConversationCreateSerializer(serializers.Serializer):
    """La familia manda solo el estudiante (el encargado es su propia
    cuenta); un docente o Dirección eligen también el encargado (RF-38)."""

    student = serializers.SlugRelatedField(slug_field="public_id", queryset=Student.objects.all())
    guardian = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Guardian.objects.all(), required=False
    )
    subject = serializers.CharField(max_length=150)
    content = serializers.CharField()


class ConversationReplySerializer(serializers.Serializer):
    content = serializers.CharField()


class RecipientSerializer(serializers.Serializer):
    guardian = serializers.UUIDField()
    student = serializers.UUIDField()
    guardian_name = serializers.CharField()
    student_name = serializers.CharField()
    label = serializers.CharField()


class UnreadCountSerializer(serializers.Serializer):
    no_leidas = serializers.IntegerField()
