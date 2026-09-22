from apps.catalog.models import DocumentType
from apps.documents.models import IssuedDocument
from apps.documents.services.issuance import emitir_documento

from .solvency import calcular_solvencia


class EstudianteInsolvente(Exception):
    pass


def emitir_constancia_solvencia(*, enrollment, issued_by) -> IssuedDocument:
    """RF-08 / RN-08. Una constancia de solvencia solo tiene sentido si el
    estudiante de verdad está solvente al momento de emitirla — no es un
    formulario libre, es una certificación."""
    if not calcular_solvencia(enrollment=enrollment)["solvente"]:
        raise EstudianteInsolvente(
            "Este estudiante no está solvente; no se puede emitir la constancia."
        )
    tipo = DocumentType.objects.get(template_key="constancia_solvencia")
    return emitir_documento(enrollment=enrollment, document_type=tipo, issued_by=issued_by)
