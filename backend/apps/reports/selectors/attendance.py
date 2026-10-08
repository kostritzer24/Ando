"""RF-15, reporte 2: asistencia — conteo por estado, por inscripción."""

from django.db.models import Count

from apps.attendance.models import Attendance
from apps.students.models import Enrollment


def resumen_asistencia(*, cycle_id: str | None = None, section_id: str | None = None) -> list[dict]:
    inscripciones = Enrollment.objects.filter(
        is_active=True, status=Enrollment.ESTADO_ACTIVO
    ).select_related("student", "section")
    if cycle_id:
        inscripciones = inscripciones.filter(cycle__public_id=cycle_id)
    if section_id:
        inscripciones = inscripciones.filter(section__public_id=section_id)

    filas = []
    for inscripcion in inscripciones:
        conteos = dict(
            Attendance.objects.filter(enrollment=inscripcion, is_active=True)
            .values("status")
            .annotate(total=Count("id"))
            .values_list("status", "total")
        )
        if not conteos:
            continue
        filas.append(
            {
                "student_code": inscripcion.student.internal_code,
                "student_name": inscripcion.student.nombre_completo(),
                "section": str(inscripcion.section),
                "presente": conteos.get("presente", 0),
                "ausente": conteos.get("ausente", 0),
                "justificado": conteos.get("justificado", 0),
            }
        )
    return filas
