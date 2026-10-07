from django.conf import settings
from django.db import models

from apps.catalog.models import ActivityType, GradingUnit
from apps.core.models import BaseModel
from apps.scheduling.models import TeacherAssignment
from apps.students.models import Enrollment


class Activity(BaseModel):
    """Actividad evaluativa (RF-17). El tope de 100 puntos por unidad y el
    mínimo de 4 pruebas cortas (RN-01, RN-02, RN-04 revisada por
    ADR-0003) se validan en `grading/domain/unit_design.py`, no acá."""

    assignment = models.ForeignKey(
        TeacherAssignment,
        verbose_name="asignación docente",
        on_delete=models.PROTECT,
        related_name="activities",
    )
    unit = models.ForeignKey(
        GradingUnit, verbose_name="unidad", on_delete=models.PROTECT, related_name="activities"
    )
    activity_type = models.ForeignKey(
        ActivityType, verbose_name="tipo de actividad", on_delete=models.PROTECT
    )
    name = models.CharField("nombre", max_length=120)
    max_score = models.DecimalField("punteo máximo", max_digits=5, decimal_places=2)
    due_date = models.DateField("fecha de entrega")

    class Meta:
        verbose_name = "actividad"
        verbose_name_plural = "actividades"
        ordering = ["unit", "due_date"]

    def __str__(self) -> str:
        return f"{self.name} — {self.unit}"

    @property
    def es_prueba_corta(self) -> bool:
        return self.activity_type.counts_as_short_quiz


class Grade(BaseModel):
    """Calificación (RF-18). `raw_score` es el punteo real y nunca se
    sobreescribe (RN-05); `current_score` es la que entra en los
    promedios y la única que ve la familia (RN-06) — empieza igual a
    `raw_score` y solo cambia cuando se aprueba una
    `GradeChangeRequest`."""

    ORIGEN_MANUAL = "manual"
    ORIGEN_PLANTILLA = "plantilla"
    ORIGENES = [(ORIGEN_MANUAL, "Manual"), (ORIGEN_PLANTILLA, "Plantilla")]

    enrollment = models.ForeignKey(
        Enrollment, verbose_name="inscripción", on_delete=models.PROTECT, related_name="grades"
    )
    activity = models.ForeignKey(
        Activity, verbose_name="actividad", on_delete=models.PROTECT, related_name="grades"
    )
    raw_score = models.DecimalField("punteo real", max_digits=5, decimal_places=2)
    current_score = models.DecimalField("nota vigente", max_digits=5, decimal_places=2)
    source = models.CharField("origen", max_length=20, choices=ORIGENES, default=ORIGEN_MANUAL)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="registrado por",
        on_delete=models.PROTECT,
        related_name="grades_recorded",
    )

    class Meta:
        verbose_name = "calificación"
        verbose_name_plural = "calificaciones"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["enrollment", "activity"], name="calificacion_unica"),
        ]

    def __str__(self) -> str:
        return f"{self.enrollment} — {self.activity} — {self.current_score}"


class GradeChangeRequest(BaseModel):
    """Modificación de nota (RF-10, RF-23, RN-05). El punteo real
    (`Grade.raw_score`) nunca se toca — solo `Grade.current_score`, y
    solo cuando esta solicitud queda aprobada."""

    ESTADO_PENDIENTE = "pendiente"
    ESTADO_APROBADA = "aprobada"
    ESTADO_RECHAZADA = "rechazada"
    ESTADOS = [
        (ESTADO_PENDIENTE, "Pendiente"),
        (ESTADO_APROBADA, "Aprobada"),
        (ESTADO_RECHAZADA, "Rechazada"),
    ]

    grade = models.ForeignKey(
        Grade, verbose_name="calificación", on_delete=models.PROTECT, related_name="change_requests"
    )
    original_score = models.DecimalField("nota original", max_digits=5, decimal_places=2)
    requested_score = models.DecimalField("nota propuesta", max_digits=5, decimal_places=2)
    reason = models.TextField("motivo")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="solicitado por",
        on_delete=models.PROTECT,
        related_name="grade_change_requests_made",
    )
    status = models.CharField("estado", max_length=20, choices=ESTADOS, default=ESTADO_PENDIENTE)
    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="autorizado por",
        on_delete=models.PROTECT,
        related_name="grade_change_requests_authorized",
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField("fecha de decisión", null=True, blank=True)
    resolution_note = models.TextField(
        "motivo de la decisión",
        blank=True,
        help_text="Por qué Dirección la aprobó o rechazó; el docente lo ve en su bandeja.",
    )

    class Meta:
        verbose_name = "modificación de nota"
        verbose_name_plural = "modificaciones de nota"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Modificación de {self.grade} ({self.status})"


class ReportCard(BaseModel):
    """Boletín de una unidad para una inscripción (RF-09). Flujo borrador →
    aprobado → publicado. Mientras está en borrador, el contenido (curso por
    curso) se calcula en vivo con `grading/domain/scoring.py` (ADR-0003: no
    se duplica el cálculo); al aprobarlo se congela en `contenido`, que es
    lo que ve y descarga la familia."""

    ESTADO_BORRADOR = "borrador"
    ESTADO_APROBADO = "aprobado"
    ESTADO_PUBLICADO = "publicado"
    ESTADOS = [
        (ESTADO_BORRADOR, "Borrador"),
        (ESTADO_APROBADO, "Aprobado"),
        (ESTADO_PUBLICADO, "Publicado"),
    ]

    enrollment = models.ForeignKey(
        Enrollment,
        verbose_name="inscripción",
        on_delete=models.PROTECT,
        related_name="report_cards",
    )
    unit = models.ForeignKey(
        GradingUnit, verbose_name="unidad", on_delete=models.PROTECT, related_name="report_cards"
    )
    status = models.CharField("estado", max_length=20, choices=ESTADOS, default=ESTADO_BORRADOR)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="generado por",
        on_delete=models.PROTECT,
        related_name="report_cards_generated",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="aprobado por",
        on_delete=models.PROTECT,
        related_name="report_cards_approved",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField("fecha de aprobación", null=True, blank=True)
    published_at = models.DateTimeField("fecha de publicación", null=True, blank=True)
    contenido = models.JSONField(
        "contenido aprobado",
        null=True,
        blank=True,
        help_text=(
            "Las notas tal como estaban al aprobar el boletín. Es lo que se publica y se "
            "descarga: un documento oficial no cambia porque después se corrija una nota."
        ),
    )

    class Meta:
        verbose_name = "boletín"
        verbose_name_plural = "boletines"
        ordering = ["-unit", "enrollment"]
        constraints = [
            models.UniqueConstraint(fields=["enrollment", "unit"], name="boletin_unico_por_unidad"),
        ]

    def __str__(self) -> str:
        return f"Boletín de {self.enrollment} — {self.unit} ({self.status})"
