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
# Sustituciones típicas para evadir el filtro: "put0", "1diota", "m13rda".
_LEET = str.maketrans("013457@$", "oieastas")
_PATRON_PALABRA = re.compile(r"[a-z0-9@$]+")
_LETRAS_REPETIDAS = re.compile(r"(.)\1+")


def contiene_lenguaje_inapropiado(texto: str) -> bool:
    """Compara sin acentos ni mayúsculas, palabra completa — "estúpido" y
    "ESTUPIDO" coinciden con "estupido" en la lista, pero "estupidez" no
    (coincidencia de palabra completa, no de subcadena). También detecta
    cambios de letra por número ("put0") y letras repetidas ("puuuta")."""
    palabras = _PATRON_PALABRA.findall(texto.lower().translate(_ACENTOS))
    for palabra in palabras:
        normal = palabra.translate(_LEET)
        # "puuuta" cuenta igual que "puta".
        if normal in _PALABRAS_INAPROPIADAS or (
            _LETRAS_REPETIDAS.sub(r"\1", normal) in _PALABRAS_INAPROPIADAS
        ):
            return True
    return False
