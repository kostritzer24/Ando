"""
Helpers transversales que la capa de servicios de cualquier app importa
directamente (nunca por señales de Django) — ver
docs/adr/0004-bitacora-de-cambios-formato.md.
"""

from .models import AccessLog, AuditLog


def registrar_cambio(
    *,
    usuario,
    entidad_nombre: str,
    entidad_id: int,
    accion: str,
    valor_anterior: dict | None = None,
    valor_nuevo: dict | None = None,
) -> AuditLog:
    """Escribe un registro de bitácora. Se llama desde dentro de la misma
    transacción que el cambio que audita (RNF-06)."""
    return AuditLog.objects.create(
        user=usuario,
        entity_name=entidad_nombre,
        entity_id=entidad_id,
        action=accion,
        old_value=valor_anterior,
        new_value=valor_nuevo,
    )


def registrar_acceso(*, usuario, pantalla: str) -> AccessLog:
    """Escribe un registro de acceso (RNF-07)."""
    return AccessLog.objects.create(user=usuario, screen_viewed=pantalla)
