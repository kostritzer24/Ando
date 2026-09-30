"""Reglas para editar una cuenta desde administración (RF-01).

Sin Django a propósito: son decisiones sobre quién edita a quién, que se
prueban sin base de datos."""


class CambioNoPermitido(Exception):
    """El cambio dejaría a la persona sin poder administrar su propia
    cuenta, o sin poder entrar al sistema."""


def validar_cambio_propio(*, es_la_misma_cuenta: bool, desactiva: bool, cambia_rol: bool) -> None:
    """Nadie se desactiva ni se cambia el rol a sí mismo desde la
    administración de usuarios: en los dos casos podría quedarse fuera del
    sistema (o sin el permiso para deshacerlo) con un solo clic. Otra
    persona con el permiso tiene que hacerlo."""
    if not es_la_misma_cuenta:
        return
    if desactiva:
        raise CambioNoPermitido("No podés desactivar tu propia cuenta.")
    if cambia_rol:
        raise CambioNoPermitido("No podés cambiar tu propio rol.")
