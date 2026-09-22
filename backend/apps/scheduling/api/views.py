from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.core.api.mixins import RegistraAccesoMixin, ScopedQuerysetMixin
from apps.core.permissions import PermisoPorArea

from ..domain.teacher_assignment import AsignacionInvalida
from ..models import TeacherAssignment
from ..services.teacher_assignment import crear_asignacion
from .serializers import TeacherAssignmentSerializer

_ROLES_SIN_ALCANCE_LIMITADO = {"Dirección", "Coordinación", "Administrador del sistema"}


class _SoloDireccionCreaAsignaciones(BasePermission):
    """`docs/api.md` documenta `/assignments/` como `DIR (E)` únicamente
    (RF-05): aunque docentes y talleristas tengan `editar` en el área
    `horarios_calendario` para su propio horario y calendario (Fase 8),
    decidir quién da qué curso es una decisión exclusiva de Dirección."""

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.role.name == "Dirección")


class TeacherAssignmentViewSet(RegistraAccesoMixin, ScopedQuerysetMixin, viewsets.ModelViewSet):
    """RF-05. Un docente/tallerista solo ve sus propias asignaciones; el
    resto del personal administrativo las ve todas. Solo Dirección crea,
    edita o elimina asignaciones."""

    queryset = TeacherAssignment.objects.all()
    serializer_class = TeacherAssignmentSerializer
    permission_classes = [PermisoPorArea, _SoloDireccionCreaAsignaciones]
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
