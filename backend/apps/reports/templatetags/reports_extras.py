from django import template

register = template.Library()


@register.filter
def lookup(diccionario: dict, clave: str):
    """Acceso dinámico a una clave de diccionario desde la plantilla —
    `reports/tabla.html` no conoce las columnas de cada reporte de
    antemano, así que no puede usar `fila.clave` literal."""
    valor = diccionario.get(clave, "")
    return "" if valor is None else valor
