"""RF-14, sección 14.2: el código de verificación es aleatorio y no
correlativo — a propósito no se deriva de `id` ni de `public_id`, para
que no se pueda adivinar ni enumerar."""

import secrets


def generar_codigo_verificacion() -> str:
    return secrets.token_hex(6).upper()
