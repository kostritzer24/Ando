from rest_framework import generics, viewsets
from rest_framework.generics import ListAPIView

from apps.core.models import AccessLog, AuditLog
from apps.core.permissions import PermisoPorArea

from .mixins import RegistraAccesoMixin
from .serializers import AccessLogSerializer, AuditLogSerializer


class BaseAPIView(RegistraAccesoMixin, generics.GenericAPIView):
    """Vista base para toda la API: registra el acceso de cada petición
    autenticada. Las apps futuras heredan de esta clase en vez de repetir
    el mixin en cada vista nueva."""


class BaseViewSet(RegistraAccesoMixin, viewsets.GenericViewSet):
    """Igual que `BaseAPIView`, para ViewSets."""


class AuditLogListView(RegistraAccesoMixin, ListAPIView):
    """GET /audit-log/ — bitácora de cambios. Solo Dirección y
    Administrador (docs/permisos-roles.md)."""

    queryset = AuditLog.objects.select_related("user").order_by("-created_at")
    serializer_class = AuditLogSerializer
    permission_classes = [PermisoPorArea]
    area = "bitacora_registro_acceso"

    def get_queryset(self):
        queryset = super().get_queryset()
        entity_name = self.request.query_params.get("entity")
        entity_id = self.request.query_params.get("entity_id")
        if entity_name:
            queryset = queryset.filter(entity_name=entity_name)
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        return queryset


class AccessLogListView(RegistraAccesoMixin, ListAPIView):
    """GET /access-log/ — registro de accesos. Solo Dirección y
    Administrador (docs/permisos-roles.md)."""

    queryset = AccessLog.objects.select_related("user").order_by("-accessed_at")
    serializer_class = AccessLogSerializer
    permission_classes = [PermisoPorArea]
    area = "bitacora_registro_acceso"

    def get_queryset(self):
        queryset = super().get_queryset()
        user_id = self.request.query_params.get("user")
        if user_id:
            queryset = queryset.filter(user__public_id=user_id)
        return queryset
