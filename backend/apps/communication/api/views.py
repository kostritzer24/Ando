from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from weasyprint import HTML

from apps.catalog.api.serializers import SectionSerializer
from apps.catalog.models import SchoolCycle, Section
from apps.core.api.mixins import RegistraAccesoMixin, ScopedQuerysetMixin
from apps.core.permissions import PermisoPorArea
from apps.students.models import Enrollment, Guardian, GuardianStudentLink

from ..domain.announcement import AvisoAjeno, PublicacionDeAvisoInvalida
from ..models import Announcement, ConductReport, Conversation
from ..services.announcement import (
    actualizar_aviso,
    avisos_vigentes,
    crear_aviso,
    retirar_aviso,
)
from ..services.buzon import (
    CuentaBloqueada,
    DestinatarioInvalido,
    LenguajeInapropiado,
    buscar_destinatarios,
    con_no_leido,
    contar_no_leidas,
    iniciar_conversacion,
    marcar_leida,
    responder,
)
from ..services.conduct_report import (
    ReporteYaPublicado,
    contenido_reporte,
    crear_reporte,
    publicar_reporte,
)
from .serializers import (
    AnnouncementSerializer,
    ConductReportCreateSerializer,
    ConductReportSerializer,
    ConversationCreateSerializer,
    ConversationDetailSerializer,
    ConversationReplySerializer,
    ConversationSerializer,
    MessageSerializer,
    RecipientSerializer,
    UnreadCountSerializer,
)

_ROLES_SIN_ALCANCE_LIMITADO = {"Dirección", "Coordinación"}
ROL_DIRECCION = "Dirección"
_ROLES_DOCENTES = {"Docente", "Tallerista"}


def _secciones_del_docente(user):
    from apps.scheduling.models import TeacherAssignment

    return TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list(
        "section_id", flat=True
    )


def _secciones_a_cargo_o_asignadas(user):
    """Secciones donde un docente puede actuar en el buzón y en los
    reportes de conducta: las que tiene asignadas (cualquier curso) y
    aquella de la que figura como docente a cargo."""
    from apps.catalog.models import Section

    return set(_secciones_del_docente(user)) | set(
        Section.objects.filter(homeroom_teacher=user).values_list("id", flat=True)
    )


def _secciones_de_la_familia(user):
    return Enrollment.objects.filter(
        student__guardian_links__guardian__user=user,
        student__guardian_links__is_active=True,
        is_active=True,
        status=Enrollment.ESTADO_ACTIVO,
    ).values_list("section_id", flat=True)


class AnnouncementViewSet(RegistraAccesoMixin, ScopedQuerysetMixin, viewsets.ModelViewSet):
    """RF-13/RF-36. Publican Dirección y los docentes (los roles con `E` en
    el área); un docente solo edita y retira lo que publicó (RN-18). El
    resto de los roles con acceso al área solo ven los avisos vigentes que
    les corresponden por destinatario."""

    queryset = Announcement.objects.select_related("published_by")
    serializer_class = AnnouncementSerializer
    permission_classes = [PermisoPorArea]
    area = "avisos"
    lookup_field = "public_id"

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        if user.role.name in _ROLES_DOCENTES:
            # Los propios se ven siempre, aunque estén vencidos o vayan a
            # otra sección: si no, el docente no podría administrarlos.
            return queryset.filter(
                Q(published_by=user)
                | (
                    Q(id__in=avisos_vigentes(queryset).values("id"))
                    & (
                        Q(audience=Announcement.AUDIENCIA_TODOS)
                        | Q(target_section_id__in=_secciones_del_docente(user))
                    )
                )
            ).distinct()
        queryset = avisos_vigentes(queryset)
        if user.role.name == "Padre de familia":
            return queryset.filter(
                Q(audience=Announcement.AUDIENCIA_TODOS)
                | Q(target_section_id__in=_secciones_de_la_familia(user))
            ).distinct()
        return queryset.none()

    def create(self, request, *args, **kwargs):
        serializer = AnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            aviso = crear_aviso(published_by=request.user, **serializer.validated_data)
        except PublicacionDeAvisoInvalida as exc:
            raise ValidationError(str(exc)) from exc
        return Response(
            AnnouncementSerializer(aviso, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        try:
            actualizar_aviso(
                serializer.instance, usuario=self.request.user, cambios=serializer.validated_data
            )
        except AvisoAjeno as exc:
            raise PermissionDenied(str(exc)) from exc
        except PublicacionDeAvisoInvalida as exc:
            raise ValidationError(str(exc)) from exc

    def perform_destroy(self, instance):
        try:
            retirar_aviso(instance, usuario=self.request.user)
        except AvisoAjeno as exc:
            raise PermissionDenied(str(exc)) from exc

    @extend_schema(responses=SectionSerializer(many=True))
    @action(detail=False, methods=["get"], url_path="target-sections")
    def target_sections(self, request):
        """Secciones a las que se puede dirigir un aviso: las vigentes del
        ciclo activo. Va por el área `avisos` y no por el catálogo, que el
        docente no tiene (excepción documentada en CLAUDE.md)."""
        if request.user.role.permissions.get("avisos") != "editar":
            raise PermissionDenied("No puedes publicar avisos.")
        secciones = Section.objects.filter(
            is_active=True, cycle__status=SchoolCycle.ESTADO_ACTIVO
        ).select_related("cycle")
        return Response(SectionSerializer(secciones, many=True).data)


class ConductReportViewSet(
    RegistraAccesoMixin,
    ScopedQuerysetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """RF-24/RF-35. `guide_teacher` es el docente que firma: quien levanta
    el reporte, o el docente a cargo de la sección si lo registra
    Dirección."""

    queryset = ConductReport.objects.all()
    permission_classes = [PermisoPorArea]
    area = "reportes_conducta"
    lookup_field = "public_id"

    def get_serializer_class(self):
        return ConductReportCreateSerializer if self.action == "create" else ConductReportSerializer

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        if user.role.name == "Docente":
            return queryset.filter(enrollment__section_id__in=_secciones_a_cargo_o_asignadas(user))
        if user.role.name == "Padre de familia":
            # Como el boletín: la familia solo ve lo que Dirección publicó.
            return queryset.filter(
                status=ConductReport.ESTADO_PUBLICADO,
                enrollment__student__guardian_links__guardian__user=user,
                enrollment__student__guardian_links__is_active=True,
            ).distinct()
        return queryset.none()

    @action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, public_id=None):
        """POST /conduct-reports/{public_id}/publish/ — solo Dirección."""
        if request.user.role.name != ROL_DIRECCION:
            raise PermissionDenied("Solo Dirección publica los reportes de conducta.")
        reporte = self.get_object()
        try:
            publicar_reporte(reporte, published_by=request.user)
        except ReporteYaPublicado as exc:
            raise ValidationError(str(exc)) from exc
        return Response(ConductReportSerializer(reporte).data)

    def create(self, request, *args, **kwargs):
        serializer = ConductReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        enrollment = datos.pop("enrollment")
        # `article_ids` ya llega resuelto a instancias reales de
        # `ConductRuleArticle` (SlugRelatedField) — acá se pasa su clave
        # primaria, nunca su `public_id`, que es lo que espera el atajo
        # `article_id=` del FK en `ConductReportArticle`.
        article_ids = [a.id for a in datos.pop("article_ids", [])]

        # Quien firma es el docente que levanta el reporte. Si lo registra
        # Dirección, firma el docente a cargo de la sección (o, si no hay,
        # Dirección misma).
        if request.user.role.name == "Docente":
            if enrollment.section_id not in _secciones_a_cargo_o_asignadas(request.user):
                raise PermissionDenied(
                    "Solo un docente de esa sección puede registrar este reporte."
                )
            guide_teacher = request.user
        else:
            guide_teacher = enrollment.section.homeroom_teacher or request.user

        reporte = crear_reporte(
            enrollment=enrollment,
            guide_teacher=guide_teacher,
            direction_member=request.user if request.user.role.name == ROL_DIRECCION else None,
            article_ids=article_ids,
            **datos,
        )
        return Response(ConductReportSerializer(reporte).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, public_id=None):
        """RF-24: el PDF reproduce el formato real del centro
        (`docs/reporte.docx`, ADR-0006), con las líneas de firma en
        blanco (RN-15)."""
        reporte = self.get_object()
        contexto = contenido_reporte(reporte)
        html = render_to_string("communication/reporte_conducta.html", contexto)
        pdf_bytes = HTML(string=html).write_pdf()
        nombre_archivo = (
            f"reporte_conducta_{reporte.enrollment.student.internal_code}_{reporte.report_date}.pdf"
        )
        return HttpResponse(
            pdf_bytes,
            content_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
        )


class ConversationViewSet(
    RegistraAccesoMixin,
    ScopedQuerysetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """RF-25/RF-37/RF-38, RN-19. Ven la conversación el encargado al que
    pertenece, los docentes de la sección, quien la inició y Dirección;
    todos ellos responden. La bandeja va del último mensaje al primero,
    con el "no leído" de quien consulta."""

    queryset = Conversation.objects.select_related(
        "student", "guardian", "section", "created_by"
    ).filter(is_active=True)
    permission_classes = [PermisoPorArea]
    area = "buzon"
    lookup_field = "public_id"

    def get_serializer_class(self):
        if self.action == "create":
            return ConversationCreateSerializer
        if self.action == "retrieve":
            return ConversationDetailSerializer
        return ConversationSerializer

    def scope_queryset(self, queryset, user):
        if user.role.name == ROL_DIRECCION:
            return queryset
        if user.role.name == "Docente":
            return queryset.filter(
                Q(section_id__in=_secciones_a_cargo_o_asignadas(user)) | Q(created_by=user)
            )
        if user.role.name == "Padre de familia":
            return queryset.filter(guardian__user=user)
        return queryset.none()

    def get_queryset(self):
        return con_no_leido(super().get_queryset(), self.request.user).order_by("-last_message_at")

    def retrieve(self, request, *args, **kwargs):
        conversacion = self.get_object()
        marcar_leida(conversacion, request.user)
        conversacion.no_leido = False
        return Response(ConversationDetailSerializer(conversacion).data)

    @extend_schema(request=ConversationCreateSerializer, responses=ConversationDetailSerializer)
    def create(self, request, *args, **kwargs):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        if request.user.role.name == "Padre de familia":
            # RF-37: la familia escribe sobre sus propios hijos, siempre
            # como su propia cuenta.
            guardian = Guardian.objects.filter(user=request.user).first()
            vinculado = (
                guardian
                and GuardianStudentLink.objects.filter(
                    guardian=guardian, student=datos["student"], is_active=True
                ).exists()
            )
            if not vinculado:
                raise PermissionDenied("Ese estudiante no está vinculado a tu cuenta.")
        elif request.user.role.name in {ROL_DIRECCION, "Docente"}:
            guardian = datos.get("guardian")
            if guardian is None:
                raise ValidationError({"guardian": "Elige el encargado al que le escribes."})
        else:
            raise PermissionDenied("Tu rol no puede iniciar conversaciones.")
        try:
            conversacion = iniciar_conversacion(
                creada_por=request.user,
                guardian=guardian,
                student=datos["student"],
                subject=datos["subject"],
                content=datos["content"],
            )
        except (LenguajeInapropiado, CuentaBloqueada, DestinatarioInvalido) as exc:
            raise ValidationError(str(exc)) from exc
        conversacion.no_leido = False
        return Response(
            ConversationDetailSerializer(conversacion).data, status=status.HTTP_201_CREATED
        )

    @extend_schema(request=ConversationReplySerializer, responses=MessageSerializer)
    @action(detail=True, methods=["post"], url_path="reply")
    def reply(self, request, public_id=None):
        """Cualquier participante con acceso a la conversación responde."""
        conversacion = self.get_object()
        serializer = ConversationReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            mensaje = responder(
                conversation=conversacion,
                sender=request.user,
                content=serializer.validated_data["content"],
            )
        except (LenguajeInapropiado, CuentaBloqueada) as exc:
            raise ValidationError(str(exc)) from exc
        return Response(MessageSerializer(mensaje).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=UnreadCountSerializer)
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        """El contador del menú del buzón."""
        base = self.scope_queryset(Conversation.objects.filter(is_active=True), request.user)
        return Response({"no_leidas": contar_no_leidas(base, request.user)})

    @extend_schema(
        parameters=[OpenApiParameter("q", str, description="Nombre del encargado o del alumno")],
        responses=RecipientSerializer(many=True),
    )
    @action(detail=False, methods=["get"], url_path="recipients")
    def recipients(self, request):
        """RF-38: a quién puede escribirle un docente o Dirección."""
        if request.user.role.name not in {ROL_DIRECCION, "Docente"}:
            raise PermissionDenied("Tu rol no puede iniciar conversaciones.")
        return Response(buscar_destinatarios(request.query_params.get("q", "")))
