from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.mixins import RegistraAccesoMixin, ScopedQuerysetMixin
from apps.core.permissions import PermisoPorArea

from ..domain.calendar_event import PublicacionInvalida, puede_editar
from ..domain.day_structure import PeriodoInvalido
from ..domain.teacher_assignment import AsignacionInvalida
from ..models import CalendarEvent, ScheduleBlock, TeacherAssignment
from ..services.calendar_event import crear_evento
from ..services.schedule_block import CruceDeHorario, crear_bloque
from ..services.teacher_assignment import crear_asignacion
from .serializers import (
    CalendarEventSerializer,
    ScheduleBlockSerializer,
    TeacherAssignmentSerializer,
)

_ROLES_SIN_ALCANCE_LIMITADO = {"Dirección", "Coordinación", "Administrador del sistema"}
_ROLES_DOCENTES = {"Docente", "Docente con sección a cargo", "Tallerista"}
ROL_DIRECCION = "Dirección"


class _SoloDireccionEscribe(BasePermission):
    """`docs/api.md` documenta `/assignments/` y `/schedule-blocks/` como
    `DIR (E)` únicamente: aunque docentes y talleristas tengan `editar`
    en el área `horarios_calendario` para su propio horario y calendario,
    armar el horario y decidir quién da qué curso son decisiones
    exclusivas de Dirección."""

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.role.name == ROL_DIRECCION)


class TeacherAssignmentViewSet(RegistraAccesoMixin, ScopedQuerysetMixin, viewsets.ModelViewSet):
    """RF-05. Un docente/tallerista solo ve sus propias asignaciones; el
    resto del personal administrativo las ve todas. Solo Dirección crea,
    edita o elimina asignaciones."""

    queryset = TeacherAssignment.objects.all()
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [PermisoPorArea, _SoloDireccionEscribe]
    area = "horarios_calendario"
    lookup_field = "public_id"

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        return queryset.filter(teacher=user)

    def perform_create(self, serializer):
        try:
            serializer.instance = crear_asignacion(**serializer.validated_data)
        except AsignacionInvalida as exc:
            raise ValidationError({"course": str(exc)}) from exc


class ScheduleBlockViewSet(RegistraAccesoMixin, ScopedQuerysetMixin, viewsets.ModelViewSet):
    """RF-06 / HU-06. Solo Dirección arma o modifica el horario."""

    queryset = ScheduleBlock.objects.all()
    serializer_class = ScheduleBlockSerializer
    permission_classes = [PermisoPorArea, _SoloDireccionEscribe]
    area = "horarios_calendario"
    lookup_field = "public_id"

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        return queryset.filter(assignment__teacher=user)

    def perform_create(self, serializer):
        try:
            serializer.instance = crear_bloque(**serializer.validated_data)
        except (PeriodoInvalido, CruceDeHorario) as exc:
            raise ValidationError(str(exc)) from exc


class CalendarEventViewSet(RegistraAccesoMixin, ScopedQuerysetMixin, viewsets.ModelViewSet):
    """RF-22 / RN-17. Cada docente/tallerista edita solo lo que publicó;
    Dirección edita todo el calendario."""

    queryset = CalendarEvent.objects.all()
    serializer_class = CalendarEventSerializer
    permission_classes = [PermisoPorArea]
    area = "horarios_calendario"
    lookup_field = "public_id"

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        if user.role.name in _ROLES_DOCENTES:
            return queryset.filter(Q(published_by=user) | Q(type=CalendarEvent.TIPO_INSTITUCIONAL))
        return queryset.none()

    def perform_create(self, serializer):
        try:
            serializer.instance = crear_evento(
                published_by=self.request.user, **serializer.validated_data
            )
        except PublicacionInvalida as exc:
            raise ValidationError(str(exc)) from exc

    def _requiere_permiso_de_edicion(self, evento: CalendarEvent) -> None:
        if not puede_editar(
            is_direccion=self.request.user.role.name == ROL_DIRECCION,
            published_by_id=evento.published_by_id,
            user_id=self.request.user.id,
        ):
            raise PermissionDenied("Solo podés editar los eventos que vos publicaste.")

    def perform_update(self, serializer):
        self._requiere_permiso_de_edicion(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._requiere_permiso_de_edicion(instance)
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


class MyScheduleView(RegistraAccesoMixin, APIView):
    """GET /schedule/mine/ — RF-26 (podría tener): horario propio del
    docente autenticado."""

    permission_classes = [PermisoPorArea]
    area = "horarios_calendario"

    @extend_schema(
        responses={
            200: {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "public_id": {"type": "string", "format": "uuid"},
                        "day_of_week": {"type": "string"},
                        "period_number": {"type": "integer"},
                        "course": {"type": "string"},
                        "section": {"type": "string"},
                    },
                },
            }
        }
    )
    def get(self, request):
        if request.user.role.name not in _ROLES_DOCENTES:
            raise PermissionDenied(
                "Este horario es solo para docentes, maestros guía y talleristas."
            )
        bloques = ScheduleBlock.objects.filter(
            assignment__teacher=request.user, is_active=True
        ).select_related("assignment__course", "assignment__section")
        return Response(
            [
                {
                    "public_id": bloque.public_id,
                    "day_of_week": bloque.day_of_week,
                    "period_number": bloque.period_number,
                    "course": bloque.assignment.course.name,
                    "section": str(bloque.assignment.section),
                }
                for bloque in bloques
            ]
        )
