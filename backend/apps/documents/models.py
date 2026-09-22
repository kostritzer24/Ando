from django.conf import settings
from django.db import models

from apps.catalog.models import DocumentType
from apps.core.models import BaseModel
from apps.students.models import Enrollment


class IssuedDocument(BaseModel):
    """Documento emitido (RF-08, RF-11, RF-14). El contenido del PDF no se
    guarda como datos estructurados aparte: se genera desde la plantilla
    HTML de `document_type.template_key` con los datos vigentes de
    `enrollment` en el momento de emitir, y el PDF resultante es lo único
    que se conserva (`file`). `verification_code` es aleatorio y no
    correlativo (sección 14.2) — es lo único que la página pública de
    verificación (RF-14) recibe, nunca el `public_id` interno."""

    document_type = models.ForeignKey(
        DocumentType,
        verbose_name="tipo de documento",
        on_delete=models.PROTECT,
        related_name="issued_documents",
    )
    enrollment = models.ForeignKey(
        Enrollment,
        verbose_name="inscripción",
        on_delete=models.PROTECT,
        related_name="issued_documents",
    )
    verification_code = models.CharField(
        "código de verificación", max_length=20, unique=True, editable=False
    )
    file = models.FileField("archivo", upload_to="documentos_emitidos/")
    custom_text = models.TextField(
        "texto libre",
        blank=True,
        help_text="Solo se usa en cartas membretadas; las constancias tienen redacción fija.",
    )
    issued_at = models.DateTimeField("fecha de emisión", auto_now_add=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="emitido por",
        on_delete=models.PROTECT,
        related_name="documents_issued",
    )

    class Meta:
        verbose_name = "documento emitido"
        verbose_name_plural = "documentos emitidos"
        ordering = ["-issued_at"]
        indexes = [models.Index(fields=["verification_code"])]

    def __str__(self) -> str:
        return f"{self.document_type} — {self.enrollment} ({self.verification_code})"
