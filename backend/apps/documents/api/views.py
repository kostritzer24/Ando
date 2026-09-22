from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.api.mixins import RegistraAccesoMixin, ScopedQuerysetMixin
from apps.core.permissions import PermisoPorArea

from ..models import IssuedDocument
from ..services.issuance import TipoDeDocumentoNoPermitido, emitir_documento_general
from .serializers import DocumentIssueSerializer, IssuedDocumentSerializer

_ROLES_SIN_ALCANCE_LIMITADO = {"Dirección", "Coordinación", "Administrador del sistema"}
ROL_DIRECCION = "Dirección"
ROL_PAGOS = "Encargado de pagos"


def _documentos_alcanzados(user):
    if user.role.name in _ROLES_SIN_ALCANCE_LIMITADO:
        return IssuedDocument.objects.all()
    if user.role.name == ROL_PAGOS:
        # Nota 1 de docs/permisos-roles.md: el alcance de Pagos sobre
        # "Documentos emitidos" es solo lo necesario para facturar y
        # emitir constancias de solvencia, no cualquier documento.
        return IssuedDocument.objects.filter(document_type__template_key="constancia_solvencia")
    if user.role.name == "Padre de familia":
        return IssuedDocument.objects.filter(
            enrollment__student__guardian_links__guardian__user=user,
            enrollment__student__guardian_links__is_active=True,
        ).distinct()
    return IssuedDocument.objects.none()


class DocumentIssueView(RegistraAccesoMixin, APIView):
    """POST /documents/issue/ — RF-11. `docs/api.md` lo documenta como
    `DIR (E)` únicamente: aunque la nota 1 de la matriz le da a Pagos
    edición sobre "Documentos emitidos", ese alcance es solo para la
    constancia de solvencia (que tiene su propio endpoint en `payments`),
    no para constancias de estudio/conducta ni cartas membretadas."""

    permission_classes = [PermisoPorArea]
    area = "documentos"

    @extend_schema(request=DocumentIssueSerializer, responses={200: OpenApiTypes.BINARY})
    def post(self, request):
        if request.user.role.name != ROL_DIRECCION:
            raise ValidationError("Solo Dirección emite este tipo de documento.")

        serializer = DocumentIssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            documento = emitir_documento_general(
                issued_by=request.user, **serializer.validated_data
            )
        except TipoDeDocumentoNoPermitido as exc:
            raise ValidationError(str(exc)) from exc

        documento.file.open("rb")
        contenido = documento.file.read()
        documento.file.close()
        return HttpResponse(
            contenido,
            content_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{documento.verification_code}.pdf"'
            },
        )


class IssuedDocumentViewSet(
    RegistraAccesoMixin, ScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet
):
    """RF-08 / RF-11: consultar y volver a descargar documentos ya
    emitidos, sin tener que regenerarlos."""

    queryset = IssuedDocument.objects.all()
    serializer_class = IssuedDocumentSerializer
    permission_classes = [PermisoPorArea]
    area = "documentos"
    lookup_field = "public_id"

    def scope_queryset(self, queryset, user):
        return _documentos_alcanzados(user)

    @action(detail=True, methods=["get"], url_path="download")
    def download(self, request, public_id=None):
        documento = self.get_object()
        documento.file.open("rb")
        contenido = documento.file.read()
        documento.file.close()
        return HttpResponse(
            contenido,
            content_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{documento.verification_code}.pdf"'
            },
        )


class VerifyDocumentView(APIView):
    """GET /verify/{verification_code}/ — RF-14 / HU-14. La única ruta
    pública sin sesión de todo el contrato (sección 14.2), con límite de
    tasa dedicado para impedir el barrido."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "verificacion_qr"

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "tipo_documento": {"type": "string"},
                    "fecha": {"type": "string", "format": "date"},
                    "estudiante": {"type": "string"},
                },
            }
        }
    )
    def get(self, request, verification_code):
        documento = get_object_or_404(
            IssuedDocument.objects.filter(is_active=True), verification_code=verification_code
        )
        return Response(
            {
                "tipo_documento": documento.document_type.name,
                "fecha": documento.issued_at.date(),
                "estudiante": documento.enrollment.student.nombre_completo(),
            }
        )
