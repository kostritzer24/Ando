from decimal import Decimal

from apps.students.models import Enrollment

from ..domain.scoring import calcular_nota_unidad
from ..models import Activity, Grade


class PunteoFueraDeRango(Exception):
    pass


class YaCalificado(Exception):
    """RN-05/RN-07: el punteo real nunca se sobreescribe. Una vez que hay
    una `Grade`, cualquier cambio pasa por `GradeChangeRequest` — ya sea
    que venga de un formulario o de una plantilla re-cargada."""


def _validar_rango(raw_score: Decimal, activity: Activity) -> None:
    if not (Decimal("0") <= raw_score <= activity.max_score):
        raise PunteoFueraDeRango(
            f"El punteo debe estar entre 0 y {activity.max_score} para '{activity.name}'."
        )


def registrar_punteo(
    *,
    enrollment: Enrollment,
    activity: Activity,
    raw_score: Decimal,
    recorded_by,
    source: str = Grade.ORIGEN_MANUAL,
) -> Grade:
    """RF-18. Primera vez que se califica esa actividad para esa
    inscripción — si ya existe, ver `YaCalificado`."""
    _validar_rango(raw_score, activity)
    if Grade.objects.filter(enrollment=enrollment, activity=activity, is_active=True).exists():
        raise YaCalificado(f"{enrollment} ya tiene una nota para '{activity.name}'.")
    return Grade.objects.create(
        enrollment=enrollment,
        activity=activity,
        raw_score=raw_score,
        current_score=raw_score,
        source=source,
        recorded_by=recorded_by,
    )


def nota_de_unidad(*, enrollment: Enrollment, unit, assignment) -> Decimal:
    """RF-18 / RF-09. Suma de las notas vigentes (`current_score`) de las
    actividades ya calificadas de esa unidad, para un curso (`assignment`)
    puntual — parcial si el curso todavía no tiene todas sus actividades
    calificadas. El tope de 100 puntos (RN-01) es por curso, así que hace
    falta filtrar por `assignment`, no solo por unidad: una inscripción
    tiene actividades de varios cursos a la vez en la misma unidad."""
    calificaciones = Grade.objects.filter(
        enrollment=enrollment,
        activity__unit=unit,
        activity__assignment=assignment,
        is_active=True,
    ).values_list("current_score", flat=True)
    return calcular_nota_unidad(list(calificaciones))
