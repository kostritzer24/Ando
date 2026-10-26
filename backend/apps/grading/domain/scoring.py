"""RN-02 (nota final = promedio de las 4 unidades, redondeado sin
decimales — ADR-0003: redondeo aritmético estándar, mitad hacia arriba)
y RN-03 (60 puntos mínimos para aprobar). Única función que calcula la
nota de unidad y la nota final en todo el sistema — no se duplica en boletín, reporte,
portal público ni puntos faltantes (ADR-0003, consecuencias)."""

from decimal import ROUND_HALF_UP, Decimal

NOTA_MINIMA_APROBACION = 60
CENTAVO = Decimal("0.01")


def calcular_nota_unidad(
    punteos: list[Decimal], *, puntos_evaluados: Decimal | None = None
) -> Decimal:
    """RF-18: la nota de unidad es la suma de los punteos vigentes de
    cada actividad ya calificada (cada una vale de su propio máximo,
    y todas juntas suman 100 cuando la unidad está completa).

    RF-40 / RN-22: si la unidad está promediada, `puntos_evaluados` es la
    suma de los punteos máximos de sus actividades vigentes y la nota es
    lo obtenido sobre esos puntos, llevado a 100 (dos decimales, mitad
    hacia arriba como el resto del sistema, ADR-0003). Única fórmula de la
    nota de unidad: boletín, consolidado, reportes y portal la reusan."""
    suma = sum(punteos, Decimal("0"))
    if puntos_evaluados is None:
        return suma
    if puntos_evaluados <= 0:
        return Decimal("0.00")
    return (suma * 100 / puntos_evaluados).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def calcular_nota_final(notas_unidad: list[Decimal]) -> int:
    if not notas_unidad:
        raise ValueError("Hace falta al menos una nota de unidad para calcular la nota final.")
    promedio = sum(notas_unidad, Decimal("0")) / len(notas_unidad)
    return int(promedio.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def aprueba_curso(nota_final: int) -> bool:
    return nota_final >= NOTA_MINIMA_APROBACION
