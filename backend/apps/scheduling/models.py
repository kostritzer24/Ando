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
