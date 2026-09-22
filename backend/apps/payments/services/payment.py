from apps.core.services import registrar_cambio

from ..models import Payment


def registrar_pago(
    *,
    enrollment,
    period_month: int,
    period_year: int,
    amount,
    payment_date,
    receipt_number,
    recorded_by,
) -> Payment:
    """RF-07 / HU-07. Las restricciones de unicidad (un pago por mes por
    inscripción, número de recibo único) las hace la base de datos —
    acá solo se abre la bitácora (RNF-06: notas, pagos y asistencia)."""
    pago = Payment.objects.create(
        enrollment=enrollment,
        period_month=period_month,
        period_year=period_year,
        amount=amount,
        payment_date=payment_date,
        receipt_number=receipt_number,
        recorded_by=recorded_by,
    )
    registrar_cambio(
        usuario=recorded_by,
        entidad_nombre="Payment",
        entidad_id=pago.id,
        accion="crear",
        valor_nuevo={
            "enrollment": str(enrollment.public_id),
            "period_month": period_month,
            "period_year": period_year,
            "amount": str(amount),
            "receipt_number": receipt_number,
        },
    )
    return pago
