from django.conf import settings
from django.db import models

from apps.catalog.models import Scholarship, SchoolCycle, Section
from apps.core.models import BaseModel


class Student(BaseModel):
    """Estudiante. `internal_code` lo asigna siempre el sistema (RN-14) —
    nunca se recibe del cliente, ver `students/domain/internal_code.py`.
    `health_notes`/`socioeconomic_notes` son de acceso reservado (RNF-04):
    se sirven desde un serializer aparte, nunca desde el general."""

    internal_code = models.CharField("código interno", max_length=10, unique=True, editable=False)
    first_name = models.CharField("nombres", max_length=100)
    last_name = models.CharField("apellidos", max_length=100)
    birth_date = models.DateField("fecha de nacimiento")
    address = models.TextField("dirección", blank=True)
    previous_institution = models.CharField("institución anterior", max_length=150, blank=True)
    health_notes = models.TextField("datos de salud", blank=True)
    socioeconomic_notes = models.TextField("datos socioeconómicos", blank=True)

    class Meta:
        verbose_name = "estudiante"
        verbose_name_plural = "estudiantes"
        ordering = ["last_name", "first_name"]
        indexes = [models.Index(fields=["internal_code"])]

    def __str__(self) -> str:
        return f"{self.internal_code} — {self.first_name} {self.last_name}"

    def nombre_completo(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Guardian(BaseModel):
    """Encargado. Una cuenta (`user`) es siempre de un solo encargado, y
    ese encargado puede estar vinculado a varios estudiantes
    (`GuardianStudentLink`) — es la "cuenta familiar" del ADR-0002."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        on_delete=models.PROTECT,
        related_name="guardian",
    )
    full_name = models.CharField("nombre completo", max_length=150)
    phone = models.CharField("teléfono", max_length=30, blank=True)
    messaging_number = models.CharField("número de mensajería", max_length=30, blank=True)
    occupation = models.CharField("oficio", max_length=100, blank=True)

    class Meta:
        verbose_name = "encargado"
        verbose_name_plural = "encargados"
        ordering = ["full_name"]

    def __str__(self) -> str:
        return self.full_name


class GuardianStudentLink(BaseModel):
    """Vínculo encargado↔estudiante (ADR-0002). El parentesco vive acá,
    no en `Guardian`, porque puede ser distinto por cada estudiante
    vinculado a la misma cuenta."""

    guardian = models.ForeignKey(
        Guardian, verbose_name="encargado", on_delete=models.PROTECT, related_name="student_links"
    )
    student = models.ForeignKey(
        Student, verbose_name="estudiante", on_delete=models.PROTECT, related_name="guardian_links"
    )
    relationship = models.CharField("parentesco", max_length=60)
    is_primary = models.BooleanField("encargado principal", default=False)

    class Meta:
        verbose_name = "vínculo encargado-estudiante"
        verbose_name_plural = "vínculos encargado-estudiante"
        constraints = [
            models.UniqueConstraint(fields=["guardian", "student"], name="vinculo_unico"),
        ]

    def __str__(self) -> str:
        return f"{self.guardian} — {self.student} ({self.relationship})"


class Enrollment(BaseModel):
    """Inscripción — el centro del modelo (sección 8 del prompt maestro):
    todo lo académico, de asistencia, de pagos y de documentos cuelga de
    acá, no directamente de `Student`."""

    ESTADO_ACTIVO = "activo"
    ESTADO_RETIRADO = "retirado"
    ESTADO_GRADUADO = "graduado"
    ESTADO_TRASLADADO = "trasladado"
    ESTADOS = [
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_RETIRADO, "Retirado"),
        (ESTADO_GRADUADO, "Graduado"),
        (ESTADO_TRASLADADO, "Trasladado"),
    ]

    student = models.ForeignKey(
        Student, verbose_name="estudiante", on_delete=models.PROTECT, related_name="enrollments"
    )
    section = models.ForeignKey(
        Section, verbose_name="sección", on_delete=models.PROTECT, related_name="enrollments"
    )
    cycle = models.ForeignKey(
        SchoolCycle,
        verbose_name="ciclo escolar",
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    scholarship = models.ForeignKey(
        Scholarship,
        verbose_name="beca",
        on_delete=models.PROTECT,
        related_name="enrollments",
        null=True,
        blank=True,
    )
    status = models.CharField("estado", max_length=20, choices=ESTADOS, default=ESTADO_ACTIVO)
    enrolled_at = models.DateField("fecha de inscripción")

    class Meta:
        verbose_name = "inscripción"
        verbose_name_plural = "inscripciones"
        ordering = ["-cycle", "student"]
        constraints = [
            # HU-03: no se puede inscribir dos veces al mismo estudiante
            # en el mismo ciclo.
            models.UniqueConstraint(
                fields=["student", "cycle"], name="inscripcion_unica_por_ciclo"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.student} — {self.section} ({self.cycle})"
