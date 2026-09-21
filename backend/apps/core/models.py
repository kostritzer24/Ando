import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Bitácora de cambios (RNF-06). De solo escritura: nunca se modifica ni
    se borra un registro ya creado — ver docs/adr/0004-bitacora-de-cambios-formato.md."""

    ACCION_CREAR = "crear"
    ACCION_ACTUALIZAR = "actualizar"
    ACCION_ELIMINAR = "eliminar"
    ACCIONES = [
        (ACCION_CREAR, "Crear"),
        (ACCION_ACTUALIZAR, "Actualizar"),
        (ACCION_ELIMINAR, "Eliminar"),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        on_delete=models.PROTECT,
        related_name="cambios_registrados",
    )
    entity_name = models.CharField("entidad afectada", max_length=100)
    entity_id = models.PositiveIntegerField("id de la entidad")
    action = models.CharField("acción", max_length=20, choices=ACCIONES)
    old_value = models.JSONField("valor anterior", null=True, blank=True)
    new_value = models.JSONField("valor nuevo", null=True, blank=True)
    created_at = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        verbose_name = "registro de bitácora"
        verbose_name_plural = "bitácora de cambios"
        indexes = [
            models.Index(fields=["entity_name", "entity_id", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_action_display()} {self.entity_name}#{self.entity_id}"


class AccessLog(models.Model):
    """Registro de acceso (RNF-07): usuario, fecha y pantalla consultada.
    Alimenta los indicadores del estudio. De solo escritura."""

    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        on_delete=models.PROTECT,
        related_name="accesos_registrados",
    )
    screen_viewed = models.CharField("pantalla consultada", max_length=255)
    accessed_at = models.DateTimeField("fecha", auto_now_add=True)

    class Meta:
        verbose_name = "registro de acceso"
        verbose_name_plural = "registro de accesos"
        indexes = [
            models.Index(fields=["user", "accessed_at"]),
            models.Index(fields=["accessed_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.screen_viewed}"
