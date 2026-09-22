from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class SchoolCycle(BaseModel):
    """Ciclo escolar — dato maestro 1 de 7 (sección 9 del prompt maestro)."""

    ESTADO_PLANIFICADO = "planificado"
    ESTADO_ACTIVO = "activo"
    ESTADO_CERRADO = "cerrado"
    ESTADOS = [
        (ESTADO_PLANIFICADO, "Planificado"),
        (ESTADO_ACTIVO, "Activo"),
        (ESTADO_CERRADO, "Cerrado"),
    ]

    year = models.PositiveIntegerField("año", unique=True)
    start_date = models.DateField("fecha de inicio")
    end_date = models.DateField("fecha de cierre")
    status = models.CharField("estado", max_length=20, choices=ESTADOS, default=ESTADO_PLANIFICADO)

    class Meta:
        verbose_name = "ciclo escolar"
        verbose_name_plural = "ciclos escolares"
        ordering = ["-year"]

    def __str__(self) -> str:
        return str(self.year)


class GradingUnit(BaseModel):
    """Unidad — parte del dato maestro 1 (ciclos y unidades). Las fechas
    de entrega de notas y habilitación del boletín se calculan siempre
    a partir de `end_date` (RN-10, ver `catalog/domain/grading_unit.py`),
    nunca se escriben a mano."""

    cycle = models.ForeignKey(
        SchoolCycle, verbose_name="ciclo escolar", on_delete=models.PROTECT, related_name="units"
    )
    number = models.PositiveSmallIntegerField("número")
    start_date = models.DateField("fecha de inicio")
    end_date = models.DateField("fecha de cierre")
    grades_due_date = models.DateField("fecha de entrega de notas")
    report_card_enabled_date = models.DateField("fecha de habilitación del boletín")

    class Meta:
        verbose_name = "unidad"
        verbose_name_plural = "unidades"
        ordering = ["cycle", "number"]
        constraints = [
            models.UniqueConstraint(fields=["cycle", "number"], name="unidad_unica_por_ciclo"),
        ]

    def __str__(self) -> str:
        return f"Unidad {self.number} — {self.cycle}"


class Section(BaseModel):
    """Sección — dato maestro 2. Cubre también las secciones de taller
    (ADR-0001): `type` distingue `academica` de `taller`, y el maestro
    guía (`homeroom_teacher`) solo aplica a las académicas."""

    TIPO_ACADEMICA = "academica"
    TIPO_TALLER = "taller"
    TIPOS = [(TIPO_ACADEMICA, "Académica"), (TIPO_TALLER, "Taller")]

    cycle = models.ForeignKey(
        SchoolCycle, verbose_name="ciclo escolar", on_delete=models.PROTECT, related_name="sections"
    )
    grade = models.CharField("grado", max_length=60)
    letter = models.CharField("letra", max_length=5, blank=True)
    type = models.CharField("tipo", max_length=20, choices=TIPOS)
    homeroom_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="maestro guía",
        on_delete=models.PROTECT,
        related_name="secciones_a_cargo",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "sección"
        verbose_name_plural = "secciones"
        ordering = ["cycle", "grade", "letter"]

    def __str__(self) -> str:
        return f"{self.grade} {self.letter}".strip()


class Course(BaseModel):
    """Curso — dato maestro 3 (incluye los talleres, ADR-0001: `type`
    distingue `academico` de `taller`)."""

    TIPO_ACADEMICO = "academico"
    TIPO_TALLER = "taller"
    TIPOS = [(TIPO_ACADEMICO, "Académico"), (TIPO_TALLER, "Taller")]

    name = models.CharField("nombre", max_length=120)
    type = models.CharField("tipo", max_length=20, choices=TIPOS)

    class Meta:
        verbose_name = "curso"
        verbose_name_plural = "cursos"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ActivityType(BaseModel):
    """Tipo de actividad evaluativa — dato maestro 4."""

    name = models.CharField("nombre", max_length=80, unique=True)
    counts_as_short_quiz = models.BooleanField(
        "cuenta como prueba corta",
        default=False,
        help_text="RN-04: se usa para exigir el mínimo de 4 pruebas cortas por unidad.",
    )

    class Meta:
        verbose_name = "tipo de actividad evaluativa"
        verbose_name_plural = "tipos de actividad evaluativa"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class JustificationType(BaseModel):
    """Tipo de justificación de falta — dato maestro 5."""

    name = models.CharField("nombre", max_length=80, unique=True)
    requires_document = models.BooleanField("requiere documento de respaldo", default=False)

    class Meta:
        verbose_name = "tipo de justificación"
        verbose_name_plural = "tipos de justificación"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class DocumentType(BaseModel):
    """Tipo de documento emitible — dato maestro 6."""

    name = models.CharField("nombre", max_length=80, unique=True)
    template_key = models.CharField(
        "plantilla",
        max_length=80,
        help_text="Identifica la plantilla de PDF de este documento (se conecta en la Fase 9).",
    )

    class Meta:
        verbose_name = "tipo de documento"
        verbose_name_plural = "tipos de documento"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Scholarship(BaseModel):
    """Beca — dato maestro 7."""

    name = models.CharField("nombre", max_length=80, unique=True)
    description = models.TextField("descripción", blank=True)

    class Meta:
        verbose_name = "beca"
        verbose_name_plural = "becas"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ConductRuleArticle(BaseModel):
    """Artículo del código de convivencia — octavo catálogo, agregado por
    ADR-0006 a partir del formato real `docs/reporte.docx`. Ese documento
    agrupa más de una disposición bajo el mismo número de artículo (por
    ejemplo, dos incisos distintos bajo "Art. 2"), así que lo único
    verdaderamente único es la combinación con la descripción."""

    chapter = models.CharField("capítulo", max_length=120)
    code = models.CharField("código", max_length=20)
    description = models.CharField("descripción", max_length=200)

    class Meta:
        verbose_name = "artículo del código de convivencia"
        verbose_name_plural = "artículos del código de convivencia"
        ordering = ["chapter", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["chapter", "code", "description"], name="articulo_unico_por_descripcion"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.description}"
