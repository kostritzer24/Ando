from django.utils import timezone

from apps.payments.services.solvency import calcular_solvencia
from apps.students.models import Enrollment

from ..domain.report_card import validar_aprobacion, validar_publicacion
from ..models import ReportCard


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
