from uuid import uuid4

from django.db import transaction

from apps.catalog.models import Section
from apps.core.services import registrar_cambio

from ..domain.fees import CUOTA_INSCRIPCION, CuotaNoDeterminada, cuota_mensual
from ..models import Payment


class PagoInvalido(Exception):
    pass


def _numero_de_recibo(pago: Payment) -> str:
    return f"REC-{pago.payment_date.year}-{pago.id:06d}"


@transaction.atomic
def registrar_pago(
    *,
    enrollment,
    concept: str = Payment.CONCEPTO_MENSUALIDAD,
    period_month: int | None = None,
    period_year: int | None = None,
    payment_date,
    recorded_by,
) -> Payment:
    """RF-07 / HU-07. El importe y el número de recibo los pone el sistema:
    la mensualidad es de Q100 en básico y Q150 en bachillerato, la
    inscripción de Q200 por ciclo, y el recibo es correlativo. Los
    estudiantes con beca completa no generan cobros, y los talleres
    tampoco (se cobra la inscripción académica)."""
    if enrollment.section.type == Section.TIPO_TALLER:
        raise PagoInvalido("Los talleres no generan cobros: registra el pago en su grado.")
    if enrollment.scholarship_id is not None:
        raise PagoInvalido("Este estudiante tiene beca completa y no genera cobros.")

    if concept == Payment.CONCEPTO_INSCRIPCION:
        monto = CUOTA_INSCRIPCION
        period_month = None
        period_year = enrollment.cycle.year
        if Payment.objects.filter(enrollment=enrollment, concept=concept).exists():
            raise PagoInvalido("La inscripción de este ciclo ya está pagada.")
    else:
        if not period_month or not period_year:
            raise PagoInvalido("Indica el mes y el año que se paga.")
        try:
            monto = cuota_mensual(enrollment.section.grade)
        except CuotaNoDeterminada as exc:
            raise PagoInvalido(str(exc)) from exc
        if Payment.objects.filter(
            enrollment=enrollment, period_year=period_year, period_month=period_month
        ).exists():
            raise PagoInvalido("Ese mes ya tiene un pago registrado.")

    pago = Payment.objects.create(
        enrollment=enrollment,
        concept=concept,
        period_month=period_month,
        period_year=period_year,
        amount=monto,
        payment_date=payment_date,
        receipt_number=f"TMP-{uuid4().hex}",
        recorded_by=recorded_by,
    )
    pago.receipt_number = _numero_de_recibo(pago)
    pago.save(update_fields=["receipt_number"])
    registrar_cambio(
        usuario=recorded_by,
        entidad_nombre="Payment",
        entidad_id=pago.id,
        accion="crear",
        valor_nuevo={
            "enrollment": str(enrollment.public_id),
            "concept": concept,
            "period_month": period_month,
            "period_year": period_year,
            "amount": str(monto),
            "receipt_number": pago.receipt_number,
        },
    )
    return pago
