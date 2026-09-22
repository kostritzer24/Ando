from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import BaseModel
from apps.students.models import Enrollment


class Payment(BaseModel):
    """Pago mensual (RF-07, HU-07). El estado de solvencia (RN-08) se
    calcula a partir de estos registros en `payments/domain/solvency.py`,
    nunca se guarda como un campo aparte que podría desincronizarse."""

    enrollment = models.ForeignKey(
        Enrollment, verbose_name="inscripción", on_delete=models.PROTECT, related_name="payments"
    )
    period_month = models.PositiveSmallIntegerField(
        "mes", validators=[MinValueValidator(1), MaxValueValidator(12)], help_text="1 a 12."
    )
    period_year = models.PositiveIntegerField("año")
    amount = models.DecimalField(
        "monto", max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    payment_date = models.DateField("fecha de pago")
    receipt_number = models.CharField("número de recibo", max_length=40, unique=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="registrado por",
        on_delete=models.PROTECT,
        related_name="payments_recorded",
    )

    class Meta:
        verbose_name = "pago"
        verbose_name_plural = "pagos"
        ordering = ["-period_year", "-period_month"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(period_month__gte=1) & models.Q(period_month__lte=12),
                name="mes_entre_1_y_12",
            ),
            models.UniqueConstraint(
                fields=["enrollment", "period_year", "period_month"], name="pago_unico_por_mes"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.enrollment} — {self.period_month}/{self.period_year}"
