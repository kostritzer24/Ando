import mimetypes
import os
import unicodedata
from urllib.parse import quote

from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from apps.core.api.mixins import RegistraAccesoMixin, ScopedQuerysetMixin
from apps.core.permissions import PermisoPorArea
from apps.scheduling.models import TeacherAssignment

from ..models import Attendance, Justification
from ..services.attendance import (
    AsistenciaYaRegistrada,
    marcar_presentes_pendientes,
    registrar_asistencia,
)
from ..services.justification import (
    JustificacionInvalida,
    crear_justificacion,
    resolver_justificacion,
)
from .serializers import (
    AttendanceCreateSerializer,
    AttendanceSerializer,
    JustificationResolveSerializer,
    JustificationSerializer,
    MarcarPresentesSerializer,
)

_ROLES_SIN_ALCANCE_LIMITADO = {
    "Dirección",
    "Coordinación",
    "Encargado de pagos",
}
_ROLES_DOCENTES = {"Docente", "Tallerista"}


def _seccion_asignada_al_docente(user, section) -> bool:
    return TeacherAssignment.objects.filter(teacher=user, section=section, is_active=True).exists()


class _SoloDireccionResuelve(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.role.name == "Dirección")


class AttendanceViewSet(RegistraAccesoMixin, ScopedQuerysetMixin, viewsets.ModelViewSet):
    """RF-16."""

    queryset = Attendance.objects.all()
    permission_classes = [PermisoPorArea]
    area = "asistencia"
    lookup_field = "public_id"

    def get_serializer_class(self):
        return AttendanceCreateSerializer if self.action == "create" else AttendanceSerializer

    def scope_queryset(self, queryset, user):
        role_name = user.role.name
        if role_name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        if role_name == "Padre de familia":
            return queryset.filter(
                enrollment__student__guardian_links__guardian__user=user,
                enrollment__student__guardian_links__is_active=True,
            ).distinct()
        if role_name in _ROLES_DOCENTES:
            return queryset.filter(
                enrollment__section__assignments__teacher=user,
                enrollment__section__assignments__is_active=True,
            ).distinct()
        return queryset.none()

    def create(self, request, *args, **kwargs):
        serializer = AttendanceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = serializer.validated_data
        enrollment = datos["enrollment"]

        if request.user.role.name in _ROLES_DOCENTES and not _seccion_asignada_al_docente(
            request.user, enrollment.section
        ):
            raise PermissionDenied("No tienes una asignación vigente en esa sección.")

        try:
            asistencia = registrar_asistencia(
                enrollment=enrollment,
                fecha=datos["date"],
                recorded_by=request.user,
                status=datos["status"],
            )
        except AsistenciaYaRegistrada as exc:
            raise ValidationError(str(exc)) from exc
        return Response(AttendanceSerializer(asistencia).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=MarcarPresentesSerializer,
        responses={200: {"type": "object", "properties": {"creadas": {"type": "integer"}}}},
    )
    @action(detail=False, methods=["post"], url_path="mark-all-present")
    def mark_all_present(self, request):
        """POST /attendance/mark-all-present/ — deja presentes a quienes aún
        no tienen asistencia ese día; después solo se corrigen las faltas."""
        serializer = MarcarPresentesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        seccion = serializer.validated_data.get("section")
        rol = request.user.role.name
        if seccion is None and rol not in _ROLES_SIN_ALCANCE_LIMITADO:
            raise ValidationError("Elige la sección de la que quieres marcar a todos presentes.")
        if (
            seccion is not None
            and rol in _ROLES_DOCENTES
            and not _seccion_asignada_al_docente(request.user, seccion)
        ):
            raise PermissionDenied("No tienes una asignación vigente en esa sección.")
        creadas = marcar_presentes_pendientes(
            fecha=serializer.validated_data["date"], recorded_by=request.user, section=seccion
        )
        return Response({"creadas": creadas})


class JustificationViewSet(RegistraAccesoMixin, ScopedQuerysetMixin, viewsets.ModelViewSet):
    """RF-12."""

    queryset = Justification.objects.all()
    serializer_class = JustificationSerializer
    permission_classes = [PermisoPorArea]
    area = "asistencia"
    lookup_field = "public_id"

    def scope_queryset(self, queryset, user):
        role_name = user.role.name
        if role_name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        if role_name == "Padre de familia":
            return queryset.filter(
                attendance__enrollment__student__guardian_links__guardian__user=user,
                attendance__enrollment__student__guardian_links__is_active=True,
            ).distinct()
        if role_name in _ROLES_DOCENTES:
            return queryset.filter(
                attendance__enrollment__section__assignments__teacher=user,
                attendance__enrollment__section__assignments__is_active=True,
            ).distinct()
        return queryset.none()

    def perform_create(self, serializer):
        try:
            serializer.instance = crear_justificacion(
                submitted_by=self.request.user, **serializer.validated_data
            )
        except JustificacionInvalida as exc:
            raise ValidationError(str(exc)) from exc

    def get_permissions(self):
        if self.action == "resolve":
            self.area = "asistencia"
            return [PermisoPorArea(), _SoloDireccionResuelve()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, public_id=None):
        """POST /justifications/{public_id}/resolve/ — RN-12: la
        resolución la decide Dirección, caso por caso."""
        justificacion = self.get_object()
        serializer = JustificationResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            resolver_justificacion(
                justificacion,
                aprobar=serializer.validated_data["aprobar"],
                resolved_by=request.user,
            )
        except JustificacionInvalida as exc:
            raise ValidationError(str(exc)) from exc
        return Response(JustificationSerializer(justificacion).data)

    @action(detail=True, methods=["get"], url_path="document")
    def document(self, request, public_id=None):
        """GET /justifications/{public_id}/document/ — el documento de
        respaldo nunca se sirve desde una URL pública (sección 14.2):
        pasa por el mismo permiso y alcance que el resto del recurso."""
        justificacion = self.get_object()
        if not justificacion.supporting_document:
            raise ValidationError("Esta justificación no tiene documento de respaldo.")
        original = justificacion.supporting_document.name.split("/")[-1]
        extension = os.path.splitext(original)[1].lower()
        estudiante = justificacion.attendance.enrollment.student
        nombre_archivo = (
            f"Justificación - {estudiante.nombre_completo()} - "
            f"{justificacion.attendance.date:%d-%m-%Y}{extension}"
        )
        tipo_contenido = mimetypes.guess_type(original)[0] or "application/octet-stream"
        ascii_ = unicodedata.normalize("NFKD", nombre_archivo).encode("ascii", "ignore").decode()
        return HttpResponse(
            justificacion.supporting_document.read(),
            content_type=tipo_contenido,
            headers={
                "Content-Disposition": (
                    f"attachment; filename=\"{ascii_}\"; filename*=UTF-8''{quote(nombre_archivo)}"
                )
            },
        )
