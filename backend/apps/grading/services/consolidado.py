from decimal import Decimal

from apps.catalog.models import GradingUnit
from apps.students.models import Enrollment, Student

from ..domain.report_card import NUMERO_DE_UNIDADES, armar_fila_cuadro
from ..domain.scoring import calcular_nota_final
from ..selectors.avance import asignaciones_que_califican
from .report_card import notas_por_curso_y_unidad


def consolidado_de_notas(student: Student) -> dict:
    """Consolidado de notas de un estudiante para el cierre de pensum: por
    cada ciclo en que estuvo inscrito, la nota final de cada curso (promedio
    de sus unidades, la misma fila del cuadro de notas), el promedio del
    año y, al final, el promedio general. Usa las notas vigentes
    (`current_score`) de todas las unidades, sin esperar a que haya boletín
    publicado: es un documento que emite Dirección."""
    anios = []
    inscripciones = (
        Enrollment.objects.filter(student=student, is_active=True)
        .select_related("section", "cycle")
        .order_by("cycle__year")
    )
    for inscripcion in inscripciones:
        unidades = list(
            GradingUnit.objects.filter(
                cycle=inscripcion.cycle, number__lte=NUMERO_DE_UNIDADES, is_active=True
            )
        )
        asignaciones = list(
            asignaciones_que_califican(secciones=[inscripcion.section], ciclos=[inscripcion.cycle])
        )
        notas = notas_por_curso_y_unidad(inscripcion, asignaciones, unidades)
        cursos = []
        for asignacion in asignaciones:
            por_unidad = {u.number: notas.get((asignacion.id, u.id)) for u in unidades}
            cursos.append({"nombre": asignacion.course.name, **armar_fila_cuadro(por_unidad)})
        finales = [Decimal(c["promedio"]) for c in cursos if c["promedio"] is not None]
        anios.append(
            {
                "ciclo_anio": inscripcion.cycle.year,
                "grado": str(inscripcion.section),
                "cursos": cursos,
                "promedio_anual": calcular_nota_final(finales) if finales else None,
            }
        )
    anuales = [Decimal(a["promedio_anual"]) for a in anios if a["promedio_anual"] is not None]
    return {
        "numeros_unidad": list(range(1, NUMERO_DE_UNIDADES + 1)),
        "anios": anios,
        "promedio_general": calcular_nota_final(anuales) if anuales else None,
    }
