from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.core.services import registrar_cambio
from apps.payments.services.solvency import calcular_solvencia
from apps.students.models import Enrollment

from ..domain.report_card import (
    NUMERO_DE_UNIDADES,
    TransicionDeBoletinInvalida,
    armar_fila_cuadro,
    nivel_del_grado,
    promedio_de_unidades,
    validar_aprobacion,
    validar_publicacion,
)
from ..domain.scoring import calcular_nota_unidad
from ..models import Grade, ReportCard
from ..selectors.avance import asignaciones_que_califican

ENTIDAD = "grading.ReportCard"


def _registrar_transicion(boletin: ReportCard, *, usuario, estado_anterior: str) -> None:
    registrar_cambio(
        usuario=usuario,
        entidad_nombre=ENTIDAD,
        entidad_id=boletin.id,
        accion="actualizar",
        valor_anterior={"status": estado_anterior},
        valor_nuevo={"status": boletin.status},
    )


@transaction.atomic
def generar_boletines(*, section, unit, generated_by) -> list[ReportCard]:
    """RF-09: genera (o deja como está, si ya existe) un boletín en
    borrador por cada inscripción activa de la sección para esa unidad.
    Un boletín que ya fue aprobado o publicado no se toca — volver a
    generar no lo regresa a borrador."""
    inscripciones = Enrollment.objects.filter(
        section=section, cycle=unit.cycle, is_active=True, status=Enrollment.ESTADO_ACTIVO
    )
    boletines = []
    for inscripcion in inscripciones:
        boletin, creado = ReportCard.objects.get_or_create(
            enrollment=inscripcion, unit=unit, defaults={"generated_by": generated_by}
        )
        if creado:
            registrar_cambio(
                usuario=generated_by,
                entidad_nombre=ENTIDAD,
                entidad_id=boletin.id,
                accion="crear",
                valor_nuevo={"status": boletin.status, "unidad": unit.number},
            )
        boletines.append(boletin)
    return boletines


@transaction.atomic
def aprobar_boletin(boletin: ReportCard, *, approved_by) -> ReportCard:
    """Aprobar congela el contenido: lo que se publica y descarga después
    es exactamente lo que Dirección revisó, aunque más tarde se apruebe una
    corrección de nota (que entonces pide generar un boletín nuevo, no
    cambia en silencio uno ya entregado)."""
    boletin = (
        ReportCard.objects.select_for_update()
        .select_related("enrollment__student", "enrollment__section", "enrollment__cycle", "unit")
        .get(pk=boletin.pk)
    )
    estado_anterior = boletin.status
    validar_aprobacion(estado_actual=boletin.status, estado_borrador=ReportCard.ESTADO_BORRADOR)
    boletin.contenido = _para_json(contenido_boletin(boletin))
    boletin.status = ReportCard.ESTADO_APROBADO
    boletin.approved_by = approved_by
    boletin.approved_at = timezone.now()
    boletin.save(update_fields=["status", "contenido", "approved_by", "approved_at", "updated_at"])
    _registrar_transicion(boletin, usuario=approved_by, estado_anterior=estado_anterior)
    return boletin


@transaction.atomic
def publicar_boletin(boletin: ReportCard, *, published_by) -> ReportCard:
    boletin = (
        ReportCard.objects.select_for_update()
        .select_related("unit", "enrollment")
        .get(pk=boletin.pk)
    )
    estado_anterior = boletin.status
    plazo_cumplido = timezone.localdate() >= boletin.unit.report_card_enabled_date
    es_solvente = calcular_solvencia(enrollment=boletin.enrollment, hasta=boletin.unit.end_date)[
        "solvente"
    ]
    validar_publicacion(
        estado_actual=boletin.status,
        estado_aprobado=ReportCard.ESTADO_APROBADO,
        plazo_cumplido=plazo_cumplido,
        es_solvente=es_solvente,
    )
    boletin.status = ReportCard.ESTADO_PUBLICADO
    boletin.published_at = timezone.now()
    boletin.save(update_fields=["status", "published_at", "updated_at"])
    _registrar_transicion(boletin, usuario=published_by, estado_anterior=estado_anterior)
    return boletin


def _boletines_de(*, section, unit, estado):
    return ReportCard.objects.filter(
        enrollment__section=section, unit=unit, status=estado, is_active=True
    ).select_related("enrollment__student")


def aprobar_boletines(*, section, unit, approved_by) -> dict:
    """Aprueba de una vez todos los borradores de la sección y unidad
    (30 estudiantes eran 30 clics por sección). Cada boletín se aprueba en
    su propia transacción: uno que no se pueda aprobar no frena al resto."""
    aprobados = 0
    for boletin in _boletines_de(section=section, unit=unit, estado=ReportCard.ESTADO_BORRADOR):
        aprobar_boletin(boletin, approved_by=approved_by)
        aprobados += 1
    return {"aprobados": aprobados}


def publicar_boletines(*, section, unit, published_by) -> dict:
    """Publica todos los aprobados que cumplen RN-09 y RN-10, y devuelve
    los que quedaron sin publicar con el motivo, para que Dirección sepa a
    quién buscar (p. ej. una familia con pagos pendientes)."""
    publicados = 0
    no_publicados = []
    for boletin in _boletines_de(section=section, unit=unit, estado=ReportCard.ESTADO_APROBADO):
        try:
            publicar_boletin(boletin, published_by=published_by)
            publicados += 1
        except TransicionDeBoletinInvalida as exc:
            no_publicados.append(
                {
                    "estudiante": boletin.enrollment.student.nombre_completo(),
                    "motivo": str(exc),
                }
            )
    return {"publicados": publicados, "no_publicados": no_publicados}


def _notas_por_curso_y_unidad(inscripcion, asignaciones, unidades) -> dict:
    """`{(assignment_id, unit_id): nota}` en una sola consulta, sumando con
    la misma función que `nota_de_unidad` (ADR-0003: no se duplica el
    cálculo, solo se agrupa)."""
    punteos = defaultdict(list)
    for asignacion_id, unidad_id, punteo in Grade.objects.filter(
        enrollment=inscripcion,
        activity__assignment__in=asignaciones,
        activity__unit__in=unidades,
        activity__is_active=True,
        is_active=True,
    ).values_list("activity__assignment_id", "activity__unit_id", "current_score"):
        punteos[(asignacion_id, unidad_id)].append(punteo)
    return {clave: calcular_nota_unidad(valores) for clave, valores in punteos.items()}


def contenido_boletin(boletin: ReportCard) -> dict:
    """RF-09 / RF-34. Formato del "Cuadro de notas" institucional: una
    fila por curso con las cuatro unidades, promedio final y A/R, la fila
    "Promedio de Unidad" y la firma del maestro guía. Solo aparecen las
    unidades con boletín publicado para esta inscripción, más la de este
    boletín: una unidad en borrador o aprobada no se le adelanta a la
    familia (RN-09/RN-10). Solo cursos académicos (ADR-0001). Las notas
    salen de una sola consulta, sumadas con la misma función que
    `nota_de_unidad` (ADR-0003)."""
    inscripcion = boletin.enrollment
    unidades_visibles = {boletin.unit.number: boletin.unit}
    for publicado in ReportCard.objects.filter(
        enrollment=inscripcion, status=ReportCard.ESTADO_PUBLICADO, is_active=True
    ).select_related("unit"):
        unidades_visibles[publicado.unit.number] = publicado.unit
    unidades_visibles = {
        numero: unidad
        for numero, unidad in unidades_visibles.items()
        if numero <= NUMERO_DE_UNIDADES
    }

    asignaciones = list(
        asignaciones_que_califican(secciones=[inscripcion.section], ciclos=[inscripcion.cycle])
    )
    notas = _notas_por_curso_y_unidad(inscripcion, asignaciones, unidades_visibles.values())
    cursos = []
    for asignacion in asignaciones:
        notas_por_unidad = {
            numero: notas.get((asignacion.id, unidad.id), calcular_nota_unidad([]))
            for numero, unidad in unidades_visibles.items()
        }
        cursos.append({"nombre": asignacion.course.name, **armar_fila_cuadro(notas_por_unidad)})

    maestro_guia = inscripcion.section.homeroom_teacher
    return {
        "estudiante_nombre": inscripcion.student.nombre_completo(),
        "estudiante_codigo": inscripcion.student.internal_code,
        "grado": inscripcion.section.grade,
        "seccion": inscripcion.section.letter,
        "nivel": nivel_del_grado(inscripcion.section.grade),
        "ciclo_anio": inscripcion.cycle.year,
        "unidad_numero": boletin.unit.number,
        "numeros_unidad": list(range(1, NUMERO_DE_UNIDADES + 1)),
        "cursos": cursos,
        "promedios": promedio_de_unidades(cursos),
        "maestro_guia": f"{maestro_guia.first_name} {maestro_guia.last_name}".strip()
        if maestro_guia
        else "",
    }


def _para_json(valor):
    """El contenido congelado se guarda en un JSONField: las notas
    (`Decimal`) pasan a texto ("85.00"), que la plantilla sigue mostrando
    igual con `floatformat`."""
    if isinstance(valor, dict):
        return {clave: _para_json(v) for clave, v in valor.items()}
    if isinstance(valor, list | tuple):
        return [_para_json(v) for v in valor]
    if isinstance(valor, Decimal):
        return str(valor)
    return valor


def contenido_para_descargar(boletin: ReportCard) -> dict:
    """El contenido congelado al aprobar. Un boletín publicado antes de que
    existiera ese congelado no lo tiene: se calcula en vivo, como antes."""
    contenido = dict(boletin.contenido or contenido_boletin(boletin))
    contenido["publicado_el"] = (
        timezone.localtime(boletin.published_at).strftime("%d/%m/%Y")
        if boletin.published_at
        else ""
    )
    return contenido
