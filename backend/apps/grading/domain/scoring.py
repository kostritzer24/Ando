"""RN-02 (nota final = promedio de las 4 unidades, redondeado sin
decimales — ADR-0003: redondeo aritmético estándar, mitad hacia arriba)
y RN-03 (60 puntos mínimos para aprobar). Única función que calcula la
nota final en todo el sistema — no se duplica en boletín, reporte,
portal público ni puntos faltantes (ADR-0003, consecuencias)."""

from decimal import ROUND_HALF_UP, Decimal

NOTA_MINIMA_APROBACION = 60


def calcular_nota_unidad(punteos: list[Decimal]) -> Decimal:
    """RF-18: la nota de unidad es la suma de los punteos vigentes de
    cada actividad ya calificada (cada una vale de su propio máximo,
    y todas juntas suman 100 cuando la unidad está completa)."""
    return sum(punteos, Decimal("0"))


def calcular_nota_final(notas_unidad: list[Decimal]) -> int:
    if not notas_unidad:
        raise ValueError("Hace falta al menos una nota de unidad para calcular la nota final.")
    promedio = sum(notas_unidad, Decimal("0")) / len(notas_unidad)
    return int(promedio.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def aprueba_curso(nota_final: int) -> bool:
    return nota_final >= NOTA_MINIMA_APROBACION
