"""RF-08 (constancia de solvencia), RF-09 (boletín — usa este mismo motor
más adelante si se decide dejarlo en PDF), RF-11 (constancias y cartas
membretadas) y RF-14 (código QR). Un solo lugar arma el PDF, genera el
código de verificación y crea el `IssuedDocument`, para que los cuatro
tipos de documento no dupliquen esta lógica cada uno por su lado."""

import base64
import io
from functools import lru_cache
from pathlib import Path

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from ..domain.verification_code import generar_codigo_verificacion
from ..models import IssuedDocument

_LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"


class TipoDeDocumentoNoPermitido(Exception):
    pass


@lru_cache(maxsize=1)
def _logo_base64() -> str:
    return base64.b64encode(_LOGO_PATH.read_bytes()).decode("ascii")


def _qr_base64(contenido: str) -> str:
    imagen = qrcode.make(contenido)
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _generar_codigo_unico() -> str:
    codigo = generar_codigo_verificacion()
    while IssuedDocument.objects.filter(verification_code=codigo).exists():
        codigo = generar_codigo_verificacion()
    return codigo


def _contexto_base(*, enrollment, codigo: str, titulo: str) -> dict:
    return {
        "titulo": titulo,
        "estudiante_nombre": enrollment.student.nombre_completo(),
        "estudiante_codigo": enrollment.student.internal_code,
        "grado_seccion": str(enrollment.section),
        "ciclo_anio": enrollment.cycle.year,
        "emitido_el": timezone.localdate().strftime("%d/%m/%Y"),
        "codigo_verificacion": codigo,
        "logo_base64": _logo_base64(),
        "qr_base64": _qr_base64(f"{settings.FRONTEND_URL}/verificar/{codigo}"),
    }


def emitir_documento(
    *, enrollment, document_type, issued_by, custom_text: str = ""
) -> IssuedDocument:
    """Motor compartido: arma el PDF desde `document_type.template_key` y
    crea el `IssuedDocument`. No valida de qué tipo es — esa decisión
    (por ejemplo, que la solvencia se emite desde su propio endpoint) la
    toma quien llama."""
    codigo = _generar_codigo_unico()
    contexto = _contexto_base(
        enrollment=enrollment, codigo=codigo, titulo=document_type.name.upper()
    )
    contexto["custom_text"] = custom_text

    html = render_to_string(f"documents/{document_type.template_key}.html", contexto)
    pdf_bytes = HTML(string=html).write_pdf()

    documento = IssuedDocument.objects.create(
        document_type=document_type,
        enrollment=enrollment,
        verification_code=codigo,
        issued_by=issued_by,
        custom_text=custom_text,
    )
    documento.file.save(f"{codigo}.pdf", ContentFile(pdf_bytes), save=True)
    return documento


def emitir_documento_general(
    *, enrollment, document_type, issued_by, custom_text: str = ""
) -> IssuedDocument:
    """POST /documents/issue/ — RF-11. La constancia de solvencia tiene su
    propio endpoint (`POST /solvency/{enrollment_id}/certificate/`, RF-08)
    porque además valida RN-08/RN-09 antes de emitir; acá se rechaza a
    propósito para que no se use este camino más corto para saltarse esa
    validación."""
    if document_type.template_key == "constancia_solvencia":
        raise TipoDeDocumentoNoPermitido(
            "La constancia de solvencia se emite desde /solvency/{enrollment}/certificate/."
        )
    if document_type.template_key == "carta_membretada" and not custom_text.strip():
        raise TipoDeDocumentoNoPermitido("La carta membretada necesita el texto que va a llevar.")
    return emitir_documento(
        enrollment=enrollment,
        document_type=document_type,
        issued_by=issued_by,
        custom_text=custom_text,
    )
