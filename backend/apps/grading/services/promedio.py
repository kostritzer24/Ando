"""RF-40 / RN-22: unidad promediada. Es un estado de la unidad para una
asignación (`UnitAveraging`), no una modificación de notas: `raw_score` y
`current_score` se conservan. La fórmula vive solo en
`domain/scoring.py`; aquí se arma, por lote, cuántos puntos se evaluaron en
cada unidad promediada para pasárselos."""

from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.core.services import registrar_cambio
from apps.scheduling.models import TeacherAssignment

from ..domain.unit_design import validar_cambio_de_promedio, validar_promedio
from ..models import Activity, ReportCard, UnitAveraging
from .activity import dar_de_baja_actividad

ENTIDAD = "grading.UnitAveraging"


def puntos_evaluados_si_promediada(asignaciones, unidades) -> dict[tuple[int, int], Decimal]:
    """`{(assignment_id, unit_id): suma de punteos máximos vigentes}`, solo
    para las unidades promediadas. Dos consultas, sin importar cuántas
    asignaciones o unidades."""
    promediadas = set(
        UnitAveraging.objects.filter(
            assignment__in=asignaciones, unit__in=unidades, averaged=True, is_active=True
        ).values_list("assignment_id", "unit_id")
    )
    if not promediadas:
        return {}
    puntos = defaultdict(lambda: Decimal("0"))
    for asignacion_id, unidad_id, total in (
        Activity.objects.filter(
            assignment_id__in={a for a, _ in promediadas},
            unit_id__in={u for _, u in promediadas},
            is_active=True,
        )
        .values("assignment_id", "unit_id")
        .annotate(total=Sum("max_score"))
        .values_list("assignment_id", "unit_id", "total")
    ):
        puntos[(asignacion_id, unidad_id)] = total or Decimal("0")
    return {clave: puntos[clave] for clave in promediadas}


def _hay_boletin_aprobado(assignment: TeacherAssignment, unit) -> bool:
    return ReportCard.objects.filter(
        enrollment__section_id=assignment.section_id,
        unit=unit,
        status__in=[ReportCard.ESTADO_APROBADO, ReportCard.ESTADO_PUBLICADO],
        is_active=True,
    ).exists()


def _puntos_evaluados(assignment, unit) -> Decimal:
    return Activity.objects.filter(assignment=assignment, unit=unit, is_active=True).aggregate(
        total=Sum("max_score")
    )["total"] or Decimal("0")


def estado_de_unidad(*, assignment: TeacherAssignment, unit) -> dict:
    promedio = UnitAveraging.objects.filter(assignment=assignment, unit=unit).first()
    return {
        "promediada": bool(promedio and promedio.averaged),
        "puntos_evaluados": _puntos_evaluados(assignment, unit),
        "bloqueada": _hay_boletin_aprobado(assignment, unit),
    }


@transaction.atomic
def cambiar_promedio_de_unidad(
    *, assignment: TeacherAssignment, unit, promediar: bool, usuario, dar_de_baja=()
) -> dict:
    """Activa o quita el promedio mientras ningún boletín de esa sección y
    unidad esté aprobado. Antes de promediar se pueden dar de baja las
    actividades que ya no se harán; `dar_de_baja_actividad` sigue
    rechazando las que tienen notas."""
    TeacherAssignment.objects.select_for_update().get(pk=assignment.pk)
    validar_cambio_de_promedio(hay_boletin_aprobado=_hay_boletin_aprobado(assignment, unit))
    for actividad in dar_de_baja:
        dar_de_baja_actividad(actividad, usuario=usuario)
    if promediar:
        validar_promedio(puntos_evaluados=_puntos_evaluados(assignment, unit))

    promedio, _ = UnitAveraging.objects.get_or_create(
        assignment=assignment, unit=unit, defaults={"changed_by": usuario}
    )
    anterior = promedio.averaged
    promedio.averaged = promediar
    promedio.changed_by = usuario
    promedio.save(update_fields=["averaged", "changed_by", "updated_at"])
    if anterior != promediar:
        registrar_cambio(
            usuario=usuario,
            entidad_nombre=ENTIDAD,
            entidad_id=promedio.id,
            accion="actualizar",
            valor_anterior={"promediada": anterior},
            valor_nuevo={
                "promediada": promediar,
                "asignacion": str(assignment.public_id),
                "unidad": str(unit.public_id),
            },
        )
    return estado_de_unidad(assignment=assignment, unit=unit)
