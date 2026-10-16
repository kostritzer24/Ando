from datetime import date

from django.db import transaction

from apps.catalog.models import Section
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


@transaction.atomic
def marcar_presentes_pendientes(
    *, fecha: date, recorded_by, section: Section | None = None
) -> int:
    """RF-16 (ronda con Dirección): deja a todos presentes y solo se corrige
    quien faltó o tiene excusa. Nunca pisa una asistencia ya registrada.
    Sin `section`, cubre todas las secciones académicas (la jornada
    matutina); los talleres se marcan sección por sección."""
    inscripciones = Enrollment.objects.filter(status=Enrollment.ESTADO_ACTIVO, is_active=True)
    if section is not None:
        inscripciones = inscripciones.filter(section=section)
    else:
        inscripciones = inscripciones.filter(
            section__type=Section.TIPO_ACADEMICA, section__is_active=True
        )
    ya_marcadas = Attendance.objects.filter(date=fecha).values_list("enrollment_id", flat=True)
    creadas = 0
    for inscripcion in inscripciones.exclude(id__in=ya_marcadas):
        registrar_asistencia(
            enrollment=inscripcion,
            fecha=fecha,
            recorded_by=recorded_by,
            status=Attendance.ESTADO_PRESENTE,
        )
        creadas += 1
    return creadas
