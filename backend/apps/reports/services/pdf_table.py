"""RF-15: los ocho reportes institucionales comparten una sola plantilla
tabular — no hace falta una por reporte, todos son "filtrar y listar"."""

from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML


def render_tabla_pdf(*, titulo: str, columnas: list[tuple[str, str]], filas: list[dict]) -> bytes:
    """`columnas` es una lista de (clave, etiqueta) — la clave indexa cada
    fila del reporte, la etiqueta es lo que se ve en el encabezado."""
    contexto = {
        "titulo": titulo,
        "columnas": columnas,
        "filas": filas,
        "generado_el": timezone.localtime().strftime("%d/%m/%Y %H:%M"),
    }
    html = render_to_string("reports/tabla.html", contexto)
    return HTML(string=html).write_pdf()
