from rest_framework.pagination import PageNumberPagination


class PaginacionEstandar(PageNumberPagination):
    """Página de 25 por omisión, ampliable por el cliente hasta 200.

    El frontend necesita listas completas (144 estudiantes, sección 1 del
    prompt maestro) para tablas con búsqueda y selectores; con páginas fijas
    de 25 las veía truncadas en silencio. `page_size` le permite pedirlas en
    una sola llamada sin gastar el límite de 120 solicitudes por minuto.
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 200
