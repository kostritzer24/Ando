from datetime import date

from django.db import transaction

from apps.core.services import registrar_cambio
from apps.students.models import Enrollment

from ..models import Attendance


class AsistenciaYaRegistrada(Exception):
    pass


@transaction.atomic
def registrar_asistencia(
    *,
    enrollment: Enrollment,
    fecha: date,
    recorded_by,
    status: str,
    source: str = Attendance.ORIGEN_MANUAL,
) -> Attendance:
    """RF-16. Una sola asistencia por estudiante y día, sin importar quién la
    marque (Dirección o cualquier docente de la sección): no es por clase."""
    if Attendance.objects.filter(enrollment=enrollment, date=fecha).exists():
        raise AsistenciaYaRegistrada(
            "Ya hay asistencia registrada para ese estudiante en esa fecha; "
            "corrígela en lugar de crearla de nuevo."
        )
    asistencia = Attendance.objects.create(
        enrollment=enrollment,
        date=fecha,
        status=status,
        source=source,
        recorded_by=recorded_by,
    )
    # RNF-06: la bitácora cubre notas, pagos y asistencia.
    registrar_cambio(
        usuario=recorded_by,
        entidad_nombre="attendance.Attendance",
        entidad_id=asistencia.id,
        accion="crear",
        valor_nuevo={
            "enrollment": str(enrollment.public_id),
            "date": str(fecha),
            "status": status,
            "source": source,
        },
    )
    return asistencia
