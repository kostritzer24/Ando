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
