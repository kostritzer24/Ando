"""RN-11: pasados cinco minutos de las ocho de la mañana el estudiante
queda tarde y pierde el primer período."""

from datetime import time

from ..models import Attendance

HORA_CORTE = time(8, 5)


def calcular_estado_por_hora_llegada(hora_llegada: time) -> str:
    """Deriva `presente`/`tarde` a partir de la hora de llegada. No decide
    `ausente` ni `justificado` — esos los elige directamente quien
    registra la asistencia (HU-16)."""
    return Attendance.ESTADO_PRESENTE if hora_llegada <= HORA_CORTE else Attendance.ESTADO_TARDE
