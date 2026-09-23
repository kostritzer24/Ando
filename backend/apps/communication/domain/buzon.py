"""RNF-10 / RN-16: el buzón filtra lenguaje inapropiado antes de guardar
un mensaje. Un mensaje que lo contiene nunca se crea — quien lo envía
queda bloqueado de forma temporal (RN-16), reusando `User.locked_until`,
el mismo campo del límite de intentos de inicio de sesión (sección 14.1).
Regla pura, sin Django."""

import re
from datetime import timedelta

DURACION_BLOQUEO = timedelta(hours=24)

# Lista curada, no exhaustiva — el filtro es una primera barrera contra el
# abuso más evidente, no un moderador de contenido completo.
_PALABRAS_INAPROPIADAS = frozenset(
    {
        "idiota",
        "estupido",
        "imbecil",
        "pendejo",
        "mierda",
        "puta",
        "puto",
        "maldito",
        "maldita",
        "cabron",
        "verga",
        "carajo",
        "hijueputa",
    }
)

_ACENTOS = str.maketrans("áéíóúñ", "aeioun")
_PATRON_PALABRA = re.compile(r"[a-z]+")


def contiene_lenguaje_inapropiado(texto: str) -> bool:
    """Compara sin acentos ni mayúsculas, palabra completa — "estúpido" y
    "ESTUPIDO" coinciden con "estupido" en la lista, pero "estupidez" no
    (coincidencia de palabra completa, no de subcadena)."""
    palabras = _PATRON_PALABRA.findall(texto.lower().translate(_ACENTOS))
    return any(palabra in _PALABRAS_INAPROPIADAS for palabra in palabras)
