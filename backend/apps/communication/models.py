from django.conf import settings
from django.db import models

from apps.catalog.models import ConductRuleArticle, Section
from apps.core.models import BaseModel
from apps.students.models import Enrollment


class Announcement(BaseModel):
    """Aviso de cartelera (RF-13/RF-36, HU-36). `expires_at` es lo que
    saca al aviso de la lista cuando ya venció — no se borra, sigue en la
    bitácora, solo deja de listarse (RF-15 / reportes de documentos
    emitidos sigue esa misma idea de no borrar historial)."""

    AUDIENCIA_TODOS = "todos"
    AUDIENCIA_SECCION = "seccion"
    AUDIENCIAS = [
        (AUDIENCIA_TODOS, "Todos"),
        (AUDIENCIA_SECCION, "Una sección"),
    ]

    title = models.CharField("título", max_length=150)
    content = models.TextField("contenido")
    audience = models.CharField("destinatario", max_length=20, choices=AUDIENCIAS)
    target_section = models.ForeignKey(
        Section,
        verbose_name="sección destinataria",
        on_delete=models.PROTECT,
        related_name="announcements",
        null=True,
        blank=True,
    )
    published_at = models.DateTimeField("fecha de publicación", auto_now_add=True)
    expires_at = models.DateTimeField("fecha de vencimiento", null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="publicado por",
        on_delete=models.PROTECT,
        related_name="announcements_published",
    )

    class Meta:
        verbose_name = "aviso"
        verbose_name_plural = "avisos"
        ordering = ["-published_at"]

    def __str__(self) -> str:
        return self.title


class ConductReport(BaseModel):
    """Reporte de conducta (RF-24/RF-35). Columnas ampliadas según el
    formato real del centro — ver docs/adr/0006-formato-reporte-conducta.md.
    Ninguna firma se guarda digital: el PDF deja las líneas en blanco
    (RN-15), igual que los documentos de `documents/`."""

    LEVE = "leve"
    GRAVE = "grave"
    MUY_GRAVE = "muy_grave"
    GRAVEDADES = [
        (LEVE, "Leve"),
        (GRAVE, "Grave"),
        (MUY_GRAVE, "Muy grave"),
    ]

    LLAMADO_VERBAL = "llamado_verbal"
    AMONESTACION_ESCRITA = "amonestacion_escrita"
    COMUNICACION_FAMILIA = "comunicacion_familia"
    SUSPENSION_EXTRACURRICULAR = "suspension_extracurricular"
    SERVICIO_COMUNITARIO = "servicio_comunitario"
    SUSPENSION_CLASES = "suspension_clases"
    EVALUACION_EXPULSION = "evaluacion_expulsion"
    OTRA_SANCION = "otra"
    SANCIONES = [
        (LLAMADO_VERBAL, "Llamado verbal"),
        (AMONESTACION_ESCRITA, "Amonestación escrita"),
        (COMUNICACION_FAMILIA, "Comunicación a la familia"),
        (SUSPENSION_EXTRACURRICULAR, "Suspensión de actividades extracurriculares"),
        (SERVICIO_COMUNITARIO, "Servicio comunitario"),
        (SUSPENSION_CLASES, "Suspensión de clases"),
        (EVALUACION_EXPULSION, "Evaluación para expulsión"),
        (OTRA_SANCION, "Otra"),
    ]

    enrollment = models.ForeignKey(
        Enrollment,
        verbose_name="inscripción",
        on_delete=models.PROTECT,
        related_name="conduct_reports",
    )
    report_date = models.DateField("fecha")
    severity = models.CharField("tipo de falta", max_length=20, choices=GRAVEDADES)
    incident_description = models.TextField("hechos ocurridos")
    immediate_actions = models.TextField("medidas inmediatas tomadas")
    other_violation_detail = models.TextField("otra falta no especificada", blank=True)
    sanction_type = models.CharField("tipo de sanción", max_length=30, choices=SANCIONES)
    sanction_detail = models.TextField("detalle de la sanción", blank=True)
    commitments = models.TextField("compromisos establecidos")
    guide_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="maestro guía",
        on_delete=models.PROTECT,
        related_name="conduct_reports_as_guide",
    )
    direction_member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="miembro de dirección",
        on_delete=models.PROTECT,
        related_name="conduct_reports_as_direction",
        null=True,
        blank=True,
    )
    articles = models.ManyToManyField(
        ConductRuleArticle, through="ConductReportArticle", related_name="conduct_reports"
    )

    class Meta:
        verbose_name = "reporte de conducta"
        verbose_name_plural = "reportes de conducta"
        ordering = ["-report_date"]

    def __str__(self) -> str:
        return f"Reporte de {self.enrollment} — {self.report_date}"


class ConductReportArticle(BaseModel):
    """Artículos del código de convivencia marcados en un reporte —
    checklist del formato original, tabla de unión de ADR-0006."""

    conduct_report = models.ForeignKey(
        ConductReport, on_delete=models.CASCADE, related_name="report_articles"
    )
    article = models.ForeignKey(ConductRuleArticle, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "artículo incumplido"
        verbose_name_plural = "artículos incumplidos"
        constraints = [
            models.UniqueConstraint(
                fields=["conduct_report", "article"], name="articulo_unico_por_reporte"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.conduct_report} — {self.article}"


class Message(BaseModel):
    """Mensaje de buzón (RF-25/RF-37, HU-25/HU-37). Un hilo es una cadena
    de mensajes enlazados por `original_message`, no un objeto de
    conversación aparte — el mensaje raíz (`original_message=None`) trae
    el `subject`; las respuestas heredan el mismo `section`. RN-16: un
    mensaje con lenguaje inapropiado nunca se crea — se rechaza en
    `communication/domain/buzon.py`, que además bloquea la cuenta de
    quien lo envió (reusa `User.locked_until`, el mismo campo del límite
    de intentos de inicio de sesión, sección 14.1)."""

    ESTADO_ENVIADO = "enviado"
    ESTADO_LEIDO = "leido"
    ESTADO_RESPONDIDO = "respondido"
    ESTADOS = [
        (ESTADO_ENVIADO, "Enviado"),
        (ESTADO_LEIDO, "Leído"),
        (ESTADO_RESPONDIDO, "Respondido"),
    ]

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="remitente",
        on_delete=models.PROTECT,
        related_name="messages_sent",
    )
    section = models.ForeignKey(
        Section, verbose_name="sección", on_delete=models.PROTECT, related_name="messages"
    )
    subject = models.CharField("asunto", max_length=150, blank=True)
    content = models.TextField("contenido")
    original_message = models.ForeignKey(
        "self",
        verbose_name="mensaje original",
        on_delete=models.PROTECT,
        related_name="replies",
        null=True,
        blank=True,
    )
    status = models.CharField("estado", max_length=20, choices=ESTADOS, default=ESTADO_ENVIADO)

    class Meta:
        verbose_name = "mensaje de buzón"
        verbose_name_plural = "mensajes de buzón"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.sender} — {self.subject or '(respuesta)'}"
