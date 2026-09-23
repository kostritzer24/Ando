"""RF-15, reporte 1: consolidado de notas. Reusa `nota_de_unidad` (RF-18)
y `calcular_nota_final` (RN-02) — ningún cálculo se duplica, el mismo
número que ve el docente en la captura es el que sale acá."""

from apps.catalog.models import GradingUnit
from apps.grading.domain.scoring import calcular_nota_final
from apps.grading.services.grade import nota_de_unidad
from apps.scheduling.models import TeacherAssignment
from apps.students.models import Enrollment


def resumen_notas(*, cycle_id: str | None = None, section_id: str | None = None) -> list[dict]:
    inscripciones = Enrollment.objects.filter(
        is_active=True, status=Enrollment.ESTADO_ACTIVO, section__type="academica"
    ).select_related("student", "section", "cycle")
    if cycle_id:
        inscripciones = inscripciones.filter(cycle__public_id=cycle_id)
    if section_id:
        inscripciones = inscripciones.filter(section__public_id=section_id)

    filas = []
    for inscripcion in inscripciones:
        unidades = list(
            GradingUnit.objects.filter(cycle=inscripcion.cycle).order_by("number")
        )
        asignaciones = TeacherAssignment.objects.filter(
            section=inscripcion.section, cycle=inscripcion.cycle, is_active=True
        ).select_related("course")
        for asignacion in asignaciones:
            notas_unidad = [
                nota_de_unidad(enrollment=inscripcion, unit=unidad, assignment=asignacion)
                for unidad in unidades
            ]
            fila = {
                "student_code": inscripcion.student.internal_code,
                "student_name": inscripcion.student.nombre_completo(),
                "section": str(inscripcion.section),
                "course": asignacion.course.name,
                "final_score": calcular_nota_final(notas_unidad) if len(unidades) == 4 else None,
            }
            for unidad, nota in zip(unidades, notas_unidad, strict=True):
                fila[f"unit_{unidad.number}_score"] = nota
            filas.append(fila)
    return filas
