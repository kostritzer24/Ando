from datetime import date, time

from apps.students.models import Enrollment

from ..domain.late_arrival import calcular_estado_por_hora_llegada
from ..models import Attendance


class FaltaEstadoOHoraDeLlegada(Exception):
    pass


def registrar_asistencia(
    *,
    enrollment: Enrollment,
    fecha: date,
    recorded_by,
    status: str | None = None,
    check_in_time: time | None = None,
    source: str = Attendance.ORIGEN_MANUAL,
) -> Attendance:
    """RF-16. Si se manda `check_in_time`, el estado se deriva de RN-11;
    si no, hay que mandar `status` directamente (HU-16: también se
    registra al final de la jornada, sin hora de llegada)."""
    if check_in_time is not None:
        status = calcular_estado_por_hora_llegada(check_in_time)
    if not status:
        raise FaltaEstadoOHoraDeLlegada("Hay que indicar el estado o la hora de llegada.")
    return Attendance.objects.create(
        enrollment=enrollment,
        date=fecha,
        status=status,
        source=source,
        recorded_by=recorded_by,
    )
