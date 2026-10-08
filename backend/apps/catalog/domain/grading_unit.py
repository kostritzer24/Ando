"""RN-10: las notas se entregan quince días después del cierre de la
unidad, y el boletín se habilita en el portal una semana después de esa
entrega. Estas dos fechas nunca se escriben a mano — se calculan siempre
a partir de la fecha de cierre, para que no puedan desalinearse."""

from datetime import date, timedelta

DIAS_ENTREGA_NOTAS = 15
DIAS_HABILITACION_BOLETIN = 7


def calcular_fecha_entrega_notas(fecha_cierre: date) -> date:
    return fecha_cierre + timedelta(days=DIAS_ENTREGA_NOTAS)


def calcular_fecha_habilitacion_boletin(fecha_entrega_notas: date) -> date:
    return fecha_entrega_notas + timedelta(days=DIAS_HABILITACION_BOLETIN)


class UnidadInvalida(ValueError):
    pass


def validar_fechas_unidad(
    *,
    start_date: date,
    end_date: date,
    cycle_start: date,
    cycle_end: date,
    otras: list[tuple[date, date]],
) -> None:
    """Las fechas de una unidad: el cierre no puede ser anterior al inicio,
    la unidad cabe dentro del ciclo y no se traslapa con otra del mismo ciclo."""
    if end_date < start_date:
        raise UnidadInvalida("La fecha de cierre no puede ser anterior a la de inicio.")
    if start_date < cycle_start or end_date > cycle_end:
        raise UnidadInvalida(
            f"Las fechas de la unidad deben estar dentro del ciclo "
            f"({cycle_start:%d/%m/%Y} a {cycle_end:%d/%m/%Y})."
        )
    for otra_inicio, otra_fin in otras:
        if start_date <= otra_fin and otra_inicio <= end_date:
            raise UnidadInvalida("Las fechas se cruzan con otra unidad del mismo ciclo.")
