from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Section
from apps.core.api.mixins import RegistraAccesoMixin, ScopedQuerysetMixin
from apps.core.permissions import PermisoPorArea
from apps.scheduling.models import TeacherAssignment

from ..models import Attendance, Justification
from ..services.attendance import (
    AsistenciaYaRegistrada,
    FaltaEstadoOHoraDeLlegada,
    registrar_asistencia,
)
from ..services.justification import crear_justificacion, resolver_justificacion
from ..services.template import SeccionNoEsDeTaller, generar_plantilla, procesar_plantilla
from .serializers import (
    AttendanceCreateSerializer,
    AttendanceSerializer,
    JustificationResolveSerializer,
    JustificationSerializer,
)

_ROLES_SIN_ALCANCE_LIMITADO = {
    "Dirección",
    "Coordinación",
    "Encargado de pagos",
    "Administrador del sistema",
}
_ROLES_DOCENTES = {"Docente", "Docente con sección a cargo", "Tallerista"}


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
            raise PermissionDenied("No tenés una asignación vigente en esa sección.")

        try:
            asistencia = registrar_asistencia(
                enrollment=enrollment,
                fecha=datos["date"],
                recorded_by=request.user,
                status=datos.get("status"),
                check_in_time=datos.get("check_in_time"),
            )
        except (FaltaEstadoOHoraDeLlegada, AsistenciaYaRegistrada) as exc:
            raise ValidationError(str(exc)) from exc
        return Response(AttendanceSerializer(asistencia).data, status=status.HTTP_201_CREATED)


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
        serializer.instance = crear_justificacion(
            submitted_by=self.request.user, **serializer.validated_data
        )

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
        resolver_justificacion(
            justificacion, aprobar=serializer.validated_data["aprobar"], resolved_by=request.user
        )
        return Response(JustificationSerializer(justificacion).data)

    @action(detail=True, methods=["get"], url_path="document")
    def document(self, request, public_id=None):
        """GET /justifications/{public_id}/document/ — el documento de
        respaldo nunca se sirve desde una URL pública (sección 14.2):
        pasa por el mismo permiso y alcance que el resto del recurso."""
        justificacion = self.get_object()
        if not justificacion.supporting_document:
            raise ValidationError("Esta justificación no tiene documento de respaldo.")
        nombre_archivo = justificacion.supporting_document.name.split("/")[-1]
        return HttpResponse(
            justificacion.supporting_document.read(),
            content_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
        )


class AttendanceTemplateDownloadView(RegistraAccesoMixin, APIView):
    """GET /attendance/template/{section_public_id}/{fecha}/ — RF-21."""

    permission_classes = [PermisoPorArea]
    area = "asistencia"

    @extend_schema(responses={200: OpenApiTypes.BINARY})
    def get(self, request, section_public_id, fecha):
        section = get_object_or_404(Section, public_id=section_public_id)
        if request.user.role.name in _ROLES_DOCENTES and not _seccion_asignada_al_docente(
            request.user, section
        ):
            raise PermissionDenied("No tenés una asignación vigente en esa sección.")
        try:
            contenido = generar_plantilla(section=section)
        except SeccionNoEsDeTaller as exc:
            raise ValidationError(str(exc)) from exc

        respuesta = HttpResponse(
            contenido,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        nombre_archivo = f"asistencia_{section.grade}_{fecha}.xlsx".replace(" ", "_")
        respuesta["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
        return respuesta


class AttendanceTemplateUploadView(RegistraAccesoMixin, APIView):
    """POST /attendance/template/upload/ — RF-21. Un solo paso: si hay
    errores, no guarda nada y los devuelve (la vista previa de la
    sección 14.4); si no hay errores, guarda directo."""

    permission_classes = [PermisoPorArea]
    area = "asistencia"
    parser_classes = [MultiPartParser]

    @extend_schema(
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "section": {"type": "string", "format": "uuid"},
                    "date": {"type": "string", "format": "date"},
                    "file": {"type": "string", "format": "binary"},
                },
                "required": ["section", "date", "file"],
            }
        },
        responses={
            201: {"type": "object", "properties": {"creados": {"type": "integer"}}},
            400: {"type": "object", "properties": {"errores": {"type": "array"}}},
        },
    )
    def post(self, request):
        section_public_id = request.data.get("section")
        fecha = request.data.get("date")
        archivo = request.FILES.get("file")

        if not (section_public_id and fecha and archivo):
            raise ValidationError("Hacen falta 'section', 'date' y 'file'.")
        if not archivo.name.lower().endswith(".xlsx"):
            raise ValidationError("El archivo debe ser un .xlsx — no se aceptan macros (.xlsm).")

        section = get_object_or_404(Section, public_id=section_public_id)

        if request.user.role.name in _ROLES_DOCENTES and not _seccion_asignada_al_docente(
            request.user, section
        ):
            raise PermissionDenied("No tenés una asignación vigente en esa sección.")

        try:
            creados, errores = procesar_plantilla(
                section=section, fecha=fecha, archivo=archivo, recorded_by=request.user
            )
        except SeccionNoEsDeTaller as exc:
            raise ValidationError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001 — archivo corrupto o que no es un .xlsx real
            raise ValidationError(f"No se pudo leer el archivo: {exc}") from exc

        if errores:
            return Response({"errores": errores}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"creados": len(creados)},
            status=status.HTTP_201_CREATED,
        )
