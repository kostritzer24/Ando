from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from weasyprint import HTML

from apps.core.api.mixins import RegistraAccesoMixin, ScopedQuerysetMixin
from apps.core.permissions import PermisoPorArea
from apps.students.models import Enrollment

from ..domain.announcement import PublicacionDeAvisoInvalida
from ..models import Announcement, ConductReport, Message
from ..services.announcement import avisos_vigentes, crear_aviso
from ..services.buzon import (
    CuentaBloqueada,
    LenguajeInapropiado,
    enviar_mensaje,
    marcar_leido,
    responder_mensaje,
)
from ..services.conduct_report import contenido_reporte, crear_reporte
from .serializers import (
    AnnouncementSerializer,
    ConductReportCreateSerializer,
    ConductReportSerializer,
    MessageReplySerializer,
    MessageSerializer,
)

_ROLES_SIN_ALCANCE_LIMITADO = {"Dirección", "Coordinación", "Administrador del sistema"}
ROL_DIRECCION = "Dirección"
_ROLES_DOCENTES = {"Docente", "Docente con sección a cargo", "Tallerista"}


def _secciones_del_docente(user):
    from apps.scheduling.models import TeacherAssignment

    return TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list(
        "section_id", flat=True
    )


def _secciones_de_la_familia(user):
    return Enrollment.objects.filter(
        student__guardian_links__guardian__user=user,
        student__guardian_links__is_active=True,
        is_active=True,
        status=Enrollment.ESTADO_ACTIVO,
    ).values_list("section_id", flat=True)


class AnnouncementViewSet(RegistraAccesoMixin, ScopedQuerysetMixin, viewsets.ModelViewSet):
    """RF-13/RF-36. Solo Dirección publica; el resto de los roles con
    acceso al área (todos salvo Pagos, según la matriz) solo ven los
    avisos vigentes que les corresponden por destinatario."""

    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [PermisoPorArea]
    area = "avisos"
    lookup_field = "public_id"

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        queryset = avisos_vigentes(queryset)
        if user.role.name in _ROLES_DOCENTES:
            return queryset.filter(
                Q(audience=Announcement.AUDIENCIA_TODOS)
                | Q(target_section_id__in=_secciones_del_docente(user))
            ).distinct()
        if user.role.name == "Padre de familia":
            return queryset.filter(
                Q(audience=Announcement.AUDIENCIA_TODOS)
                | Q(target_section_id__in=_secciones_de_la_familia(user))
            ).distinct()
        return queryset.none()

    def create(self, request, *args, **kwargs):
        if request.user.role.name != ROL_DIRECCION:
            raise PermissionDenied("Solo Dirección publica avisos.")
        serializer = AnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            aviso = crear_aviso(published_by=request.user, **serializer.validated_data)
        except PublicacionDeAvisoInvalida as exc:
            raise ValidationError(str(exc)) from exc
        return Response(AnnouncementSerializer(aviso).data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        if self.request.user.role.name != ROL_DIRECCION:
            raise PermissionDenied("Solo Dirección edita avisos.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user.role.name != ROL_DIRECCION:
            raise PermissionDenied("Solo Dirección retira avisos.")
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class ConductReportViewSet(
    RegistraAccesoMixin,
    ScopedQuerysetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """RF-24/RF-35. `guide_teacher` es siempre el maestro guía de la
    sección de la inscripción (quien firma), no necesariamente quien
    llena el formulario — Dirección también puede registrar un reporte
    de una sección que no es la suya."""

    queryset = ConductReport.objects.all()
    permission_classes = [PermisoPorArea]
    area = "reportes_conducta"
    lookup_field = "public_id"

    def get_serializer_class(self):
        return ConductReportCreateSerializer if self.action == "create" else ConductReportSerializer

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        if user.role.name == "Docente con sección a cargo":
            return queryset.filter(enrollment__section__homeroom_teacher=user)
        if user.role.name == "Padre de familia":
            return queryset.filter(
                enrollment__student__guardian_links__guardian__user=user,
                enrollment__student__guardian_links__is_active=True,
            ).distinct()
        return queryset.none()

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

        guide_teacher = enrollment.section.homeroom_teacher
        if guide_teacher is None:
            raise ValidationError("Esa sección todavía no tiene maestro guía asignado.")
        if (
            request.user.role.name == "Docente con sección a cargo"
            and guide_teacher != request.user
        ):
            raise PermissionDenied(
                "Solo el maestro guía de esa sección puede registrar este reporte."
            )

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


class MessageViewSet(
    RegistraAccesoMixin,
    ScopedQuerysetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """RF-25/RF-37. Un hilo es del encargado que lo empezó — lo ven él, el
    maestro guía de la sección y Dirección (HU-25/HU-37)."""

    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [PermisoPorArea]
    area = "buzon"
    lookup_field = "public_id"

    def scope_queryset(self, queryset, user):
        if user.role.name == ROL_DIRECCION:
            return queryset
        if user.role.name == "Docente con sección a cargo":
            return queryset.filter(section__homeroom_teacher=user)
        if user.role.name == "Padre de familia":
            return queryset.filter(
                Q(sender=user, original_message__isnull=True) | Q(original_message__sender=user)
            ).distinct()
        return queryset.none()

    def retrieve(self, request, *args, **kwargs):
        mensaje = self.get_object()
        if request.user.role.name != "Padre de familia":
            marcar_leido(mensaje)
            mensaje.refresh_from_db()
        return Response(MessageSerializer(mensaje).data)

    def create(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        seccion = serializer.validated_data["section"]
        if request.user.role.name == "Padre de familia" and seccion.id not in set(
            _secciones_de_la_familia(request.user)
        ):
            raise PermissionDenied("Esa sección no corresponde a ninguno de tus estudiantes.")
        try:
            mensaje = enviar_mensaje(
                sender=request.user,
                section=seccion,
                subject=serializer.validated_data.get("subject", ""),
                content=serializer.validated_data["content"],
            )
        except (LenguajeInapropiado, CuentaBloqueada) as exc:
            raise ValidationError(str(exc)) from exc
        return Response(MessageSerializer(mensaje).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="reply")
    def reply(self, request, public_id=None):
        hilo_raiz = get_object_or_404(
            self.get_queryset(), public_id=public_id, original_message__isnull=True
        )
        if request.user.role.name not in {ROL_DIRECCION, "Docente con sección a cargo"}:
            raise PermissionDenied("Solo la dirección o el maestro guía de la sección responden.")
        serializer = MessageReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            respuesta = responder_mensaje(
                hilo_raiz=hilo_raiz,
                sender=request.user,
                content=serializer.validated_data["content"],
            )
        except (LenguajeInapropiado, CuentaBloqueada) as exc:
            raise ValidationError(str(exc)) from exc
        return Response(MessageSerializer(respuesta).data, status=status.HTTP_201_CREATED)
