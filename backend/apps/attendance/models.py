from django.conf import settings
from django.db import models

from apps.catalog.models import JustificationType
from apps.core.models import BaseModel
from apps.students.models import Enrollment


class Attendance(BaseModel):
    """Asistencia (RF-16). Aplica igual a la jornada matutina que a los
    talleres (ADR-0001) porque ambos cuelgan de `Enrollment`."""

    ESTADO_PRESENTE = "presente"
    ESTADO_TARDE = "tarde"
    ESTADO_AUSENTE = "ausente"
    ESTADO_JUSTIFICADO = "justificado"
    ESTADOS = [
        (ESTADO_PRESENTE, "Presente"),
        (ESTADO_TARDE, "Tarde"),
        (ESTADO_AUSENTE, "Ausente"),
        (ESTADO_JUSTIFICADO, "Justificado"),
    ]

    ORIGEN_MANUAL = "manual"
    ORIGEN_PLANTILLA = "plantilla"
    ORIGENES = [(ORIGEN_MANUAL, "Manual"), (ORIGEN_PLANTILLA, "Plantilla")]

    enrollment = models.ForeignKey(
        Enrollment, verbose_name="inscripción", on_delete=models.PROTECT, related_name="attendances"
    )
    date = models.DateField("fecha")
    status = models.CharField("estado", max_length=20, choices=ESTADOS)
    source = models.CharField("origen", max_length=20, choices=ORIGENES, default=ORIGEN_MANUAL)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="registrado por",
        on_delete=models.PROTECT,
        related_name="attendances_registered",
    )

    class Meta:
        verbose_name = "asistencia"
        verbose_name_plural = "asistencias"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["enrollment", "date"], name="asistencia_unica_por_dia"),
        ]

    def __str__(self) -> str:
        return f"{self.enrollment} — {self.date} — {self.status}"


class Justification(BaseModel):
    """Justificación de falta (RF-12). RN-12: la resolución evalúa cada
    caso, nunca es automática."""

    RESOLUCION_PENDIENTE = "pendiente"
    RESOLUCION_APROBADA = "aprobada"
    RESOLUCION_RECHAZADA = "rechazada"
    RESOLUCIONES = [
        (RESOLUCION_PENDIENTE, "Pendiente"),
        (RESOLUCION_APROBADA, "Aprobada"),
        (RESOLUCION_RECHAZADA, "Rechazada"),
    ]

    attendance = models.ForeignKey(
        Attendance,
        verbose_name="asistencia",
        on_delete=models.PROTECT,
        related_name="justifications",
    )
    justification_type = models.ForeignKey(
        JustificationType, verbose_name="tipo de justificación", on_delete=models.PROTECT
    )
    reason_detail = models.TextField("motivo", blank=True)
    supporting_document = models.FileField(
        "documento de respaldo", upload_to="justificaciones/%Y/%m/", null=True, blank=True
    )
    resolution = models.CharField(
        "resolución", max_length=20, choices=RESOLUCIONES, default=RESOLUCION_PENDIENTE
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="registrado por",
        on_delete=models.PROTECT,
        related_name="justifications_submitted",
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="resuelto por",
        on_delete=models.PROTECT,
        related_name="justifications_resolved",
        null=True,
        blank=True,
    )
    resolved_at = models.DateTimeField("fecha de resolución", null=True, blank=True)

    class Meta:
        verbose_name = "justificación"
        verbose_name_plural = "justificaciones"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Justificación de {self.attendance} ({self.resolution})"
