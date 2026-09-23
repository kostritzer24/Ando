from django.utils import timezone

from apps.payments.services.solvency import calcular_solvencia
from apps.scheduling.models import TeacherAssignment
from apps.students.models import Enrollment

from ..domain.report_card import validar_aprobacion, validar_publicacion
from ..domain.scoring import NOTA_MINIMA_APROBACION
from ..models import ReportCard
from .grade import nota_de_unidad


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
        boletines.append(boletin)
    return boletines


def aprobar_boletin(boletin: ReportCard, *, approved_by) -> ReportCard:
    validar_aprobacion(estado_actual=boletin.status, estado_borrador=ReportCard.ESTADO_BORRADOR)
    boletin.status = ReportCard.ESTADO_APROBADO
    boletin.approved_by = approved_by
    boletin.approved_at = timezone.now()
    boletin.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])
    return boletin


def publicar_boletin(boletin: ReportCard) -> ReportCard:
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
    return boletin


def contenido_boletin(boletin: ReportCard) -> dict:
    """RF-34. El PDF del boletín no guarda nada aparte (ver docstring de
    `ReportCard`): se arma al momento de descargarlo, curso por curso, a
    partir de las mismas asignaciones docentes de la sección — ninguna
    calificación se duplica ni se recalcula distinto de como ya la ve el
    docente en `nota_de_unidad` (RF-18)."""
    inscripcion = boletin.enrollment
    asignaciones = TeacherAssignment.objects.filter(
        section=inscripcion.section, cycle=inscripcion.cycle, is_active=True
    ).select_related("course").order_by("course__name")
    cursos = []
    for asignacion in asignaciones:
        nota = nota_de_unidad(enrollment=inscripcion, unit=boletin.unit, assignment=asignacion)
        cursos.append(
            {
                "nombre": asignacion.course.name,
                "nota": nota,
                "aprobado": nota >= NOTA_MINIMA_APROBACION,
            }
        )
    return {
        "estudiante_nombre": inscripcion.student.nombre_completo(),
        "estudiante_codigo": inscripcion.student.internal_code,
        "grado_seccion": str(inscripcion.section),
        "ciclo_anio": inscripcion.cycle.year,
        "unidad_numero": boletin.unit.number,
        "cursos": cursos,
        "publicado_el": boletin.published_at.strftime("%d/%m/%Y") if boletin.published_at else "",
    }
