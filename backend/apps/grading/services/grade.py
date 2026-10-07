from decimal import Decimal

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.services import registrar_cambio
from apps.students.models import Enrollment

from ..domain.grade_change import validar_correccion_directa
from ..domain.scoring import calcular_nota_unidad
from ..models import Activity, Grade
from .grade_change_request import hay_solicitud_pendiente

ENTIDAD = "grading.Grade"


class PunteoFueraDeRango(Exception):
    pass


class YaCalificado(Exception):
    """RN-05/RN-07: el punteo real nunca se sobreescribe. Una vez que hay
    una `Grade`, cualquier cambio pasa por `GradeChangeRequest` — ya sea
    que venga de un formulario o de una plantilla re-cargada."""


class InscripcionAjena(Exception):
    """La inscripción no es de la sección y el ciclo de la actividad. El
    permiso sobre la asignación no alcanza: sin esta validación un docente
    podía calificar en su actividad a un estudiante de otra sección."""


def _validar_rango(raw_score: Decimal, activity: Activity) -> None:
    if not (Decimal("0") <= raw_score <= activity.max_score):
        raise PunteoFueraDeRango(
            f"El punteo debe estar entre 0 y {activity.max_score} para '{activity.name}'."
        )


def _validar_inscripcion(enrollment: Enrollment, activity: Activity) -> None:
    assignment = activity.assignment
    if (
        not enrollment.is_active
        or enrollment.section_id != assignment.section_id
        or enrollment.cycle_id != assignment.cycle_id
    ):
        raise InscripcionAjena("Ese estudiante no está inscrito en la sección de esta actividad.")
    if not activity.is_active:
        raise InscripcionAjena("Esa actividad fue dada de baja.")


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
    _validar_inscripcion(enrollment, activity)
    _validar_rango(raw_score, activity)
    if Grade.objects.filter(enrollment=enrollment, activity=activity).exists():
        raise YaCalificado(f"{enrollment} ya tiene una nota para '{activity.name}'.")
    try:
        # Savepoint propio: si otra petición registró la misma nota entre
        # la consulta de arriba y este insert, la restricción única lo
        # frena y se informa como YaCalificado, no como un error 500.
        with transaction.atomic():
            calificacion = Grade.objects.create(
                enrollment=enrollment,
                activity=activity,
                raw_score=raw_score,
                current_score=raw_score,
                source=source,
                recorded_by=recorded_by,
            )
            registrar_cambio(
                usuario=recorded_by,
                entidad_nombre=ENTIDAD,
                entidad_id=calificacion.id,
                accion="crear",
                valor_nuevo={
                    "enrollment": str(enrollment.public_id),
                    "activity": str(activity.public_id),
                    "raw_score": str(raw_score),
                    "source": source,
                },
            )
    except IntegrityError as exc:
        raise YaCalificado(f"{enrollment} ya tiene una nota para '{activity.name}'.") from exc
    return calificacion


def nota_de_unidad(*, enrollment: Enrollment, unit, assignment) -> Decimal:
    """RF-18 / RF-09. Suma de las notas vigentes (`current_score`) de las
    actividades ya calificadas de esa unidad, para un curso (`assignment`)
    puntual — parcial si el curso todavía no tiene todas sus actividades
    calificadas. El tope de 100 puntos (RN-01) es por curso, así que hace
    falta filtrar por `assignment`, no solo por unidad: una inscripción
    tiene actividades de varios cursos a la vez en la misma unidad. Solo
    cuentan actividades vigentes, igual que en el tope de 100 puntos."""
    calificaciones = Grade.objects.filter(
        enrollment=enrollment,
        activity__unit=unit,
        activity__assignment=assignment,
        activity__is_active=True,
        is_active=True,
    ).values_list("current_score", flat=True)
    return calcular_nota_unidad(list(calificaciones))


@transaction.atomic
def corregir_nota_en_plazo(grade: Grade, *, nuevo_punteo: Decimal, usuario) -> Grade:
    """RN-05 dentro del plazo de entrega (ver `puede_corregirse_sin_
    autorizacion`): el docente corrige su error de dedo sin pasar por
    Dirección. Cambia la nota vigente y queda en bitácora; el punteo real
    (`raw_score`) se conserva como se capturó."""
    grade = Grade.objects.select_for_update().select_related("activity__unit").get(pk=grade.pk)
    validar_correccion_directa(
        punteo_nuevo=nuevo_punteo,
        nota_vigente=grade.current_score,
        max_score=grade.activity.max_score,
        hoy=timezone.localdate(),
        fecha_entrega_notas=grade.activity.unit.grades_due_date,
        hay_pendiente=hay_solicitud_pendiente(grade),
    )
    anterior = grade.current_score
    grade.current_score = nuevo_punteo
    grade.save(update_fields=["current_score", "updated_at"])
    registrar_cambio(
        usuario=usuario,
        entidad_nombre=ENTIDAD,
        entidad_id=grade.id,
        accion="actualizar",
        valor_anterior={"current_score": str(anterior)},
        valor_nuevo={"current_score": str(nuevo_punteo), "motivo": "corrección dentro del plazo"},
    )
    return grade
