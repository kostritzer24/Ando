from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.mixins import RegistraAccesoMixin, ScopedQuerysetMixin
from apps.core.permissions import PermisoPorArea
from apps.students.models import Enrollment

from ..models import Payment
from ..services.certificate import EstudianteInsolvente, emitir_constancia_solvencia
from ..services.payment import registrar_pago
from ..services.solvency import calcular_solvencia
from .serializers import PaymentSerializer

_ROLES_SIN_ALCANCE_LIMITADO = {
    "Dirección",
    "Coordinación",
    "Encargado de pagos",
    "Administrador del sistema",
}


def _enrollments_alcanzados(user):
    """Mismo criterio de alcance en los tres endpoints de esta app: el
    resto del personal no llega ni siquiera aquí (área `sin_acceso`), así
    que solo hay dos casos reales: alcance completo o alcance de familia
    (sección 14.2 — nunca se compara el id de la URL contra el usuario,
    se filtra el queryset antes)."""
    if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
        return Enrollment.objects.filter(is_active=True)
    if user.role.name == "Padre de familia":
        return Enrollment.objects.filter(
            is_active=True,
            student__guardian_links__guardian__user=user,
            student__guardian_links__is_active=True,
        ).distinct()
    return Enrollment.objects.none()


class PaymentViewSet(
    RegistraAccesoMixin,
    ScopedQuerysetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """RF-07 / HU-07. Un pago registrado no se edita ni se borra desde
    acá — es un comprobante, no un borrador; una corrección real pasa por
    el proceso administrativo del centro, fuera del sistema."""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [PermisoPorArea]
    area = "pagos_solvencia"
    lookup_field = "public_id"

    def scope_queryset(self, queryset, user):
        if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
            return queryset
        if user.role.name == "Padre de familia":
            return queryset.filter(
                enrollment__student__guardian_links__guardian__user=user,
                enrollment__student__guardian_links__is_active=True,
            ).distinct()
        return queryset.none()

    def perform_create(self, serializer):
        serializer.instance = registrar_pago(
            recorded_by=self.request.user, **serializer.validated_data
        )


class SolvencyView(RegistraAccesoMixin, APIView):
    """GET /solvency/{enrollment_public_id}/ — RF-07 / RF-33 / RN-08."""

    permission_classes = [PermisoPorArea]
    area = "pagos_solvencia"

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "solvente": {"type": "boolean"},
                    "tiene_beca": {"type": "boolean"},
                    "meses_pendientes": {"type": "array", "items": {"type": "array"}},
                },
            }
        }
    )
    def get(self, request, enrollment_public_id):
        enrollment = get_object_or_404(
            _enrollments_alcanzados(request.user), public_id=enrollment_public_id
        )
        return Response(calcular_solvencia(enrollment=enrollment))


class SolvencyCertificateView(RegistraAccesoMixin, APIView):
    """POST /solvency/{enrollment_public_id}/certificate/ — RF-08."""

    permission_classes = [PermisoPorArea]
    area = "pagos_solvencia"

    @extend_schema(request=None, responses={200: OpenApiTypes.BINARY})
    def post(self, request, enrollment_public_id):
        enrollment = get_object_or_404(
            _enrollments_alcanzados(request.user), public_id=enrollment_public_id
        )
        try:
            documento = emitir_constancia_solvencia(enrollment=enrollment, issued_by=request.user)
        except EstudianteInsolvente as exc:
            raise ValidationError(str(exc)) from exc

        documento.file.open("rb")
        contenido = documento.file.read()
        documento.file.close()
        nombre_archivo = f"constancia_solvencia_{enrollment.student.internal_code}.pdf"
        return HttpResponse(
            contenido,
            content_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
        )
