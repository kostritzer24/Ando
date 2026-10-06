"""RF-09: qué le falta a cada boletín antes de aprobarlo. Un curso está
completo en la unidad cuando sus actividades suman 100 puntos (RN-02) y la
inscripción tiene nota en cada una; si no, el boletín mostraría la nota
parcial como si fuera la de la unidad. Consultas por lote (no una por
estudiante ni por curso): la bandeja de una sección lo pide para todos sus
boletines a la vez."""

from collections import defaultdict
from decimal import Decimal

from apps.catalog.models import Course
from apps.scheduling.models import TeacherAssignment

from ..domain.unit_design import MAXIMO_PUNTOS_POR_UNIDAD
from ..models import Activity, Grade


def asignaciones_que_califican(*, secciones, ciclos):
    return (
        TeacherAssignment.objects.filter(
            section__in=secciones,
            cycle__in=ciclos,
            is_active=True,
            course__type=Course.TIPO_ACADEMICO,
        )
        .select_related("course")
        .order_by("course__name")
    )


def pendientes_por_inscripcion(*, inscripciones, unit) -> dict[int, list[dict]]:
    """`{enrollment_id: [{"curso", "faltan", "diseno_completo"}, ...]}`, solo
    con los cursos incompletos; una inscripción sin pendientes no aparece."""
    inscripciones = list(inscripciones)
    if not inscripciones:
        return {}
    asignaciones = list(
        asignaciones_que_califican(
            secciones={i.section_id for i in inscripciones},
            ciclos={i.cycle_id for i in inscripciones},
        )
    )
    actividades_por_asignacion = defaultdict(list)
    for actividad in Activity.objects.filter(
        assignment__in=asignaciones, unit=unit, is_active=True
    ).only("id", "assignment_id", "max_score"):
        actividades_por_asignacion[actividad.assignment_id].append(actividad)
    calificadas = set(
        Grade.objects.filter(
            enrollment__in=inscripciones, activity__unit=unit, activity__is_active=True
        ).values_list("enrollment_id", "activity_id")
    )

    pendientes = {}
    for inscripcion in inscripciones:
        cursos = []
        for asignacion in asignaciones:
            if (asignacion.section_id, asignacion.cycle_id) != (
                inscripcion.section_id,
                inscripcion.cycle_id,
            ):
                continue
            actividades = actividades_por_asignacion[asignacion.id]
            suma = sum((a.max_score for a in actividades), Decimal("0"))
            faltan = sum(1 for a in actividades if (inscripcion.id, a.id) not in calificadas)
            diseno_completo = suma == MAXIMO_PUNTOS_POR_UNIDAD
            if faltan or not diseno_completo:
                cursos.append(
                    {
                        "curso": asignacion.course.name,
                        "faltan": faltan,
                        "diseno_completo": diseno_completo,
                    }
                )
        if cursos:
            pendientes[inscripcion.id] = cursos
    return pendientes
