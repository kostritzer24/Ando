from functools import lru_cache

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


@lru_cache(maxsize=1)
def _lista_contrasenas_comunes() -> frozenset[str]:
    try:
        contenido = settings.COMMON_PASSWORDS_ES_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return frozenset()
    return frozenset(linea.strip().lower() for linea in contenido.splitlines() if linea.strip())


class ContrasenaComunEsValidator:
    """Rechaza contraseñas de la lista de contraseñas comunes en español
    (sección 14.1: "más una lista de contraseñas comunes en español"),
    además de la lista en inglés que ya trae Django."""

    def validate(self, password: str, user=None) -> None:
        if password.lower() in _lista_contrasenas_comunes():
            raise ValidationError(
                "Esta contraseña es muy común. Elegí una distinta.",
                code="password_too_common_es",
            )

    def get_help_text(self) -> str:
        return "La contraseña no puede ser una de uso muy común en español."


TAMANO_MAXIMO_DOCUMENTO_RESPALDO = 5 * 1024 * 1024  # 5 MB

# Firma binaria (magic bytes) por formato — el tipo real del archivo se
# determina por su contenido, nunca por la extensión ni el content_type
# que declara el navegador (sección 14.4: "tipo declarado, tipo real").
_FIRMAS_POR_EXTENSION = {
    "pdf": (b"%PDF-",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
}


def validar_documento_de_respaldo(archivo: UploadedFile) -> None:
    """RF-12, sección 14.4: valida tipo declarado, tipo real (por firma
    binaria) y tamaño de la constancia que se sube para justificar una
    falta. Solo acepta PDF, JPG y PNG — los formatos razonables para una
    constancia médica o similar escaneada o fotografiada."""

    if archivo.size > TAMANO_MAXIMO_DOCUMENTO_RESPALDO:
        raise ValidationError(
            "El archivo pesa demasiado. El máximo permitido es 5 MB.",
            code="archivo_demasiado_pesado",
        )

    extension = archivo.name.rsplit(".", 1)[-1].lower() if "." in archivo.name else ""
    firmas = _FIRMAS_POR_EXTENSION.get(extension)
    if firmas is None:
        raise ValidationError(
            "Formato no permitido. Solo se aceptan archivos PDF, JPG o PNG.",
            code="extension_no_permitida",
        )

    encabezado = archivo.read(16)
    archivo.seek(0)
    if not any(encabezado.startswith(firma) for firma in firmas):
        raise ValidationError(
            "El contenido del archivo no corresponde a su extensión.",
            code="contenido_no_coincide",
        )
