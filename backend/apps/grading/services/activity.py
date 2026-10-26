from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.catalog.models import ActivityType, Course, GradingUnit
from apps.core.services import registrar_cambio
from apps.scheduling.models import TeacherAssignment

from ..domain.unit_design import (
    repartir_puntos,
    validar_baja_de_actividad,
    validar_cambio_de_punteo_maximo,
    validar_nuevo_punteo_maximo,
)
from ..models import Activity, Grade

ENTIDAD = "grading.Activity"
CAMPOS_EDITABLES = {"name", "activity_type", "max_score", "due_date"}


class AsignacionNoCalifica(Exception):
    pass


def _validar_asignacion_califica(assignment: TeacherAssignment) -> None:
    """ADR-0001, consecuencias: no se puede crear Actividad sobre una
    Asignación docente de un curso de tipo 'taller' — los talleres no
    generan calificaciones."""
    if assignment.course.type != Course.TIPO_ACADEMICO:
        raise AsignacionNoCalifica(
            "No se pueden definir actividades para un curso de taller (ADR-0001)."
        )


def _suma_de_la_unidad(assignment, unit, *, excluir_id=None) -> Decimal:
    actividades = Activity.objects.filter(assignment=assignment, unit=unit, is_active=True)
    if excluir_id is not None:
        actividades = actividades.exclude(id=excluir_id)
    return actividades.aggregate(total=Sum("max_score"))["total"] or Decimal("0")


def _tiene_notas(actividad: Activity) -> bool:
    return Grade.objects.filter(activity=actividad, is_active=True).exists()


def _foto(actividad: Activity) -> dict:
    return {
        "name": actividad.name,
        "activity_type": actividad.activity_type.name,
        "max_score": None if actividad.max_score is None else str(actividad.max_score),
        "due_date": actividad.due_date.isoformat(),
    }


@transaction.atomic
def crear_actividad(
    *,
    assignment: TeacherAssignment,
    unit: GradingUnit,
    activity_type: ActivityType,
    name: str,
    due_date: date,
    usuario,
    max_score: Decimal | None = None,
) -> Activity:
    _validar_asignacion_califica(assignment)
    # Bloquea la asignación para que dos altas simultáneas no pasen juntas
    # el tope de 100 puntos leyendo la misma suma.
    TeacherAssignment.objects.select_for_update().get(pk=assignment.pk)
    validar_nuevo_punteo_maximo(_suma_de_la_unidad(assignment, unit), max_score)
    actividad = Activity.objects.create(
        assignment=assignment,
        unit=unit,
        activity_type=activity_type,
        name=name,
        max_score=max_score,
        due_date=due_date,
    )
    registrar_cambio(
        usuario=usuario,
        entidad_nombre=ENTIDAD,
        entidad_id=actividad.id,
        accion="crear",
        valor_nuevo=_foto(actividad),
    )
    return actividad


@transaction.atomic
def actualizar_actividad(actividad: Activity, *, cambios: dict, usuario) -> Activity:
    """Solo nombre, tipo, punteo máximo y fecha. La asignación y la unidad
    no cambian: mover una actividad es crear otra en el lugar correcto."""
    TeacherAssignment.objects.select_for_update().get(pk=actividad.assignment_id)
    cambios = {campo: valor for campo, valor in cambios.items() if campo in CAMPOS_EDITABLES}
    nuevo_maximo = cambios.get("max_score", actividad.max_score)
    if nuevo_maximo != actividad.max_score:
        validar_cambio_de_punteo_maximo(tiene_notas=_tiene_notas(actividad))
        suma_sin_esta = _suma_de_la_unidad(
            actividad.assignment, actividad.unit, excluir_id=actividad.id
        )
        validar_nuevo_punteo_maximo(suma_sin_esta, nuevo_maximo)

    anterior = _foto(actividad)
    for campo, valor in cambios.items():
        setattr(actividad, campo, valor)
    actividad.save()
    registrar_cambio(
        usuario=usuario,
        entidad_nombre=ENTIDAD,
        entidad_id=actividad.id,
        accion="actualizar",
        valor_anterior=anterior,
        valor_nuevo=_foto(actividad),
    )
    return actividad


@transaction.atomic
def dar_de_baja_actividad(actividad: Activity, *, usuario) -> None:
    validar_baja_de_actividad(tiene_notas=_tiene_notas(actividad))
    actividad.is_active = False
    actividad.save(update_fields=["is_active", "updated_at"])
    registrar_cambio(
        usuario=usuario,
        entidad_nombre=ENTIDAD,
        entidad_id=actividad.id,
        accion="eliminar",
        valor_anterior=_foto(actividad),
    )


@transaction.atomic
def repartir_puntos_de_unidad(*, assignment: TeacherAssignment, unit: GradingUnit, usuario):
    """RF-39 / RN-20: las actividades con notas conservan su punteo; las
    demás se quedan con partes iguales de lo que sobra de los 100. Cada
    cambio queda en la bitácora, igual que una edición a mano."""
    TeacherAssignment.objects.select_for_update().get(pk=assignment.pk)
    actividades = list(
        Activity.objects.filter(assignment=assignment, unit=unit, is_active=True).order_by(
            "due_date", "id"
        )
    )
    calificadas = set(
        Grade.objects.filter(activity__in=actividades, is_active=True).values_list(
            "activity_id", flat=True
        )
    )
    fijas = [a for a in actividades if a.id in calificadas]
    libres = [a for a in actividades if a.id not in calificadas]
    partes = repartir_puntos([a.max_score for a in fijas], len(libres))
    for actividad, parte in zip(libres, partes, strict=True):
        if actividad.max_score == parte:
            continue
        anterior = _foto(actividad)
        actividad.max_score = parte
        actividad.save(update_fields=["max_score", "updated_at"])
        registrar_cambio(
            usuario=usuario,
            entidad_nombre=ENTIDAD,
            entidad_id=actividad.id,
            accion="actualizar",
            valor_anterior=anterior,
            valor_nuevo={**_foto(actividad), "motivo": "repartir puntos"},
        )
    return actividades
