"""RF-15/RNF-07, reporte 8: documentos emitidos."""

from apps.documents.models import IssuedDocument


def documentos_emitidos(
    *, cycle_id: str | None = None, section_id: str | None = None
) -> list[dict]:
    documentos = IssuedDocument.objects.filter(is_active=True).select_related(
        "document_type", "enrollment__student", "enrollment__section", "issued_by"
    )
    if cycle_id:
        documentos = documentos.filter(enrollment__cycle__public_id=cycle_id)
    if section_id:
        documentos = documentos.filter(enrollment__section__public_id=section_id)

    return [
        {
            "student_code": d.enrollment.student.internal_code,
            "student_name": d.enrollment.student.nombre_completo(),
            "section": str(d.enrollment.section),
            "document_type": d.document_type.name,
            "issued_at": d.issued_at,
            "issued_by": d.issued_by.username,
        }
        for d in documentos.order_by("-issued_at")
    ]
