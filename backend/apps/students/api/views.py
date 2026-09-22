from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.core.api.mixins import RegistraAccesoMixin, ScopedQuerysetMixin
from apps.core.permissions import PermisoPorArea

from ..models import Enrollment, Guardian, GuardianStudentLink, Student
from ..services.enrollment import YaInscritoEnEsteCiclo, inscribir_estudiante
from ..services.guardian import RolDeUsuarioInvalido, crear_encargado
from ..services.link import (
    VinculoYaExiste,
    desvincular_encargado_estudiante,
    vincular_encargado_estudiante,
)
from ..services.student import actualizar_datos_sensibles, crear_estudiante
from .serializers import (
    EnrollmentSerializer,
    GuardianSerializer,
    GuardianStudentLinkSerializer,
    StudentCreateSerializer,
    StudentSensitiveSerializer,
    StudentSerializer,
)

_ROLES_SIN_ALCANCE_LIMITADO = {
    "Dirección",
    "Coordinación",
    "Encargado de pagos",
    "Administrador del sistema",
}
_ROLES_DOCENTES = {"Docente", "Docente con sección a cargo", "Tallerista"}


class StudentViewSet(RegistraAccesoMixin, ScopedQuerysetMixin, viewsets.ModelViewSet):
    """RF-03. El área depende de la acción: los datos generales usan
    'estudiantes_encargados', los sensibles usan 'datos_sensibles'
    (RNF-04) — nunca el mismo permiso para ambos."""

    queryset = Student.objects.all()
    lookup_field = "public_id"

    def get_permissions(self):
        self.area = "datos_sensibles" if self.action == "sensitive" else "estudiantes_encargados"
        return [PermisoPorArea()]

    def get_serializer_class(self):
        if self.action == "create":
            return StudentCreateSerializer
        if self.action == "sensitive":
            return StudentSensitiveSerializer
        return StudentSerializer

    def scope_queryset(self, queryset, user):
        role_name = user.role.name
        if role_name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        if role_name == "Padre de familia":
            return queryset.filter(
                guardian_links__guardian__user=user, guardian_links__is_active=True
            ).distinct()
        if role_name in _ROLES_DOCENTES:
            return queryset.filter(
                enrollments__section__assignments__teacher=user,
                enrollments__section__assignments__is_active=True,
                enrollments__is_active=True,
            ).distinct()
        return queryset.none()

    def create(self, request, *args, **kwargs):
        serializer = StudentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        estudiante = crear_estudiante(**serializer.validated_data)
        return Response(StudentSerializer(estudiante).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "patch"], url_path="sensitive")
    def sensitive(self, request, public_id=None):
        """GET/PATCH /students/{public_id}/sensitive/ — RNF-04."""
        estudiante = self.get_object()
        if request.method == "GET":
            return Response(StudentSensitiveSerializer(estudiante).data)
        serializer = StudentSensitiveSerializer(estudiante, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        actualizar_datos_sensibles(estudiante, **serializer.validated_data)
        return Response(StudentSensitiveSerializer(estudiante).data)


class GuardianViewSet(RegistraAccesoMixin, viewsets.ModelViewSet):
    """RF-03/RF-04. Los encargados no se filtran por objeto (solo
    Dirección/Administrador llegan hasta acá, según la matriz de
    permisos), pero los vínculos que exponen sí importan para
    `StudentViewSet.scope_queryset`."""

    queryset = Guardian.objects.all()
    serializer_class = GuardianSerializer
    permission_classes = [PermisoPorArea]
    area = "estudiantes_encargados"
    lookup_field = "public_id"

    def perform_create(self, serializer):
        try:
            serializer.instance = crear_encargado(**serializer.validated_data)
        except RolDeUsuarioInvalido as exc:
            raise ValidationError({"user": str(exc)}) from exc

    @action(detail=True, methods=["post"], url_path="link-student")
    def link_student(self, request, public_id=None):
        """POST /guardians/{public_id}/link-student/ — RF-04."""
        guardian = self.get_object()
        serializer = GuardianStudentLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            vinculo = vincular_encargado_estudiante(guardian=guardian, **serializer.validated_data)
        except VinculoYaExiste as exc:
            raise ValidationError({"student": str(exc)}) from exc
        return Response(
            {"public_id": vinculo.public_id, "relationship": vinculo.relationship},
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"link-student/(?P<student_public_id>[0-9a-f-]+)",
    )
    def unlink_student(self, request, public_id=None, student_public_id=None):
        """DELETE /guardians/{public_id}/link-student/{student_public_id}/ — RF-04."""
        guardian = self.get_object()
        vinculo = get_object_or_404(
            GuardianStudentLink,
            guardian=guardian,
            student__public_id=student_public_id,
            is_active=True,
        )
        desvincular_encargado_estudiante(vinculo)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EnrollmentViewSet(RegistraAccesoMixin, viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [PermisoPorArea]
    area = "estudiantes_encargados"
    lookup_field = "public_id"

    def perform_create(self, serializer):
        try:
            serializer.instance = inscribir_estudiante(**serializer.validated_data)
        except YaInscritoEnEsteCiclo as exc:
            raise ValidationError({"student": str(exc)}) from exc
