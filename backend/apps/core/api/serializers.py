from rest_framework import serializers

from apps.core.models import AccessLog, AuditLog

from ..domain.pantallas import nombre_de_pantalla


class AuditLogSerializer(serializers.ModelSerializer):
    usuario = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "public_id",
            "usuario",
            "entity_name",
            "entity_id",
            "action",
            "old_value",
            "new_value",
            "created_at",
        ]
        read_only_fields = fields


class AccessLogSerializer(serializers.ModelSerializer):
    usuario = serializers.CharField(source="user.username", read_only=True)
    pantalla = serializers.SerializerMethodField()

    def get_pantalla(self, obj) -> str:
        return nombre_de_pantalla(obj.screen_viewed)

    class Meta:
        model = AccessLog
        fields = ["public_id", "usuario", "screen_viewed", "pantalla", "accessed_at"]
        read_only_fields = fields
