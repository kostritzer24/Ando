from django.conf import settings
from django.db import models

from apps.catalog.models import Course, SchoolCycle, Section
from apps.core.models import BaseModel


class TeacherAssignment(BaseModel):
    """Asignación docente (RF-05): docente/tallerista a curso-sección.
    `Course.type` debe coincidir con `Section.type` (ADR-0001), validado
    en `scheduling/domain/teacher_assignment.py`, no solo aquí."""

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="docente",
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    course = models.ForeignKey(
        Course, verbose_name="curso", on_delete=models.PROTECT, related_name="assignments"
    )
    section = models.ForeignKey(
        Section, verbose_name="sección", on_delete=models.PROTECT, related_name="assignments"
    )
    cycle = models.ForeignKey(
        SchoolCycle,
        verbose_name="ciclo escolar",
        on_delete=models.PROTECT,
        related_name="assignments",
    )

    class Meta:
        verbose_name = "asignación docente"
        verbose_name_plural = "asignaciones docentes"
        ordering = ["cycle", "section", "course"]
        constraints = [
            models.UniqueConstraint(
                fields=["teacher", "course", "section", "cycle"], name="asignacion_unica"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.teacher} — {self.course} — {self.section} ({self.cycle})"


class ScheduleBlock(BaseModel):
    """Bloque de horario (RF-06). RN-13 (seis períodos de 40 minutos) se
    valida en `scheduling/domain/day_structure.py`; el cruce de docente
    entre asignaciones distintas se valida en
    `scheduling/services/schedule_block.py`, porque necesita mirar otras
    filas, no solo esta."""

    LUNES = "lunes"
    MARTES = "martes"
    MIERCOLES = "miercoles"
    JUEVES = "jueves"
    VIERNES = "viernes"
    DIAS = [
        (LUNES, "Lunes"),
        (MARTES, "Martes"),
        (MIERCOLES, "Miércoles"),
        (JUEVES, "Jueves"),
        (VIERNES, "Viernes"),
    ]

    assignment = models.ForeignKey(
        TeacherAssignment,
        verbose_name="asignación docente",
        on_delete=models.PROTECT,
        related_name="schedule_blocks",
    )
    day_of_week = models.CharField("día", max_length=20, choices=DIAS)
    period_number = models.PositiveSmallIntegerField("período")

    class Meta:
        verbose_name = "bloque de horario"
        verbose_name_plural = "bloques de horario"
        ordering = ["day_of_week", "period_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "day_of_week", "period_number"],
                name="bloque_unico_por_asignacion",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.assignment} — {self.get_day_of_week_display()} P{self.period_number}"


class CalendarEvent(BaseModel):
    """Evento de calendario (RF-22). RN-17: cada docente edita solo lo
    que publicó; Dirección edita todo el calendario — validado en
    `scheduling/services/calendar_event.py`."""

    TIPO_INSTITUCIONAL = "institucional"
    TIPO_ASIGNACION_DOCENTE = "asignacion_docente"
    TIPOS = [
        (TIPO_INSTITUCIONAL, "Institucional"),
        (TIPO_ASIGNACION_DOCENTE, "Asignación docente"),
    ]

    title = models.CharField("título", max_length=150)
    type = models.CharField("tipo", max_length=30, choices=TIPOS)
    event_date = models.DateField("fecha")
    start_time = models.TimeField("hora de inicio")
    end_time = models.TimeField("hora de fin")
    section = models.ForeignKey(
        Section,
        verbose_name="sección",
        on_delete=models.PROTECT,
        related_name="calendar_events",
        null=True,
        blank=True,
    )
    assignment = models.ForeignKey(
        TeacherAssignment,
        verbose_name="asignación docente",
        on_delete=models.PROTECT,
        related_name="calendar_events",
        null=True,
        blank=True,
    )
    materials = models.TextField("materiales", blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="publicado por",
        on_delete=models.PROTECT,
        related_name="calendar_events_published",
    )

    class Meta:
        verbose_name = "evento de calendario"
        verbose_name_plural = "eventos de calendario"
        ordering = ["event_date", "start_time"]

    def __str__(self) -> str:
        return f"{self.title} — {self.event_date}"
