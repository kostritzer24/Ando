"""RN-14: cada estudiante tiene un código interno único, asignado siempre
por el sistema — nunca lo escribe quien inscribe. No es el código del
Ministerio de Educación (sección 2 del prompt maestro).

Formato `ES` + 3 dígitos, confirmado con la corrección numérica que
quedó documentada en `docs/modelo-datos.md` sección 6 (dos dígitos no
alcanzaban para los 144 estudiantes ya inscritos)."""

PREFIJO = "ES"
DIGITOS = 3
MAXIMO = 10**DIGITOS - 1


class CapacidadCodigoInternoAgotada(Exception):
    pass


def generar_codigo_interno(siguiente_numero: int) -> str:
    if not 1 <= siguiente_numero <= MAXIMO:
        raise CapacidadCodigoInternoAgotada(
            f"No hay más códigos internos disponibles con el formato {PREFIJO}###."
        )
    return f"{PREFIJO}{siguiente_numero:0{DIGITOS}d}"
