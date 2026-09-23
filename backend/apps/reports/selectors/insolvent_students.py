"""RF-15, reporte 3: estudiantes insolventes. Reusa `calcular_solvencia`
(RN-08) — el mismo cálculo que decide si se puede emitir la constancia
(RF-08) o publicar el boletín (RN-09), nunca uno aparte."""

from apps.payments.services.solvency import calcular_solvencia
from apps.students.models import Enrollment


def estudiantes_insolventes(
    *, cycle_id: str | None = None, section_id: str | None = None
) -> list[dict]:
    inscripciones = Enrollment.objects.filter(
        is_active=True, status=Enrollment.ESTADO_ACTIVO, section__type="academica"
    ).select_related("student", "section")
    if cycle_id:
        inscripciones = inscripciones.filter(cycle__public_id=cycle_id)
    if section_id:
        inscripciones = inscripciones.filter(section__public_id=section_id)

    filas = []
    for inscripcion in inscripciones:
        solvencia = calcular_solvencia(enrollment=inscripcion)
        if solvencia["solvente"]:
            continue
        filas.append(
            {
                "student_code": inscripcion.student.internal_code,
                "student_name": inscripcion.student.nombre_completo(),
                "section": str(inscripcion.section),
                "pending_months": len(solvencia["meses_pendientes"]),
            }
        )
    return filas
