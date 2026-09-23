class PoliticaDeSeguridadDeContenidoMiddleware:
    """Agrega `Content-Security-Policy` (sección 14.4) sin una dependencia
    nueva (regla de trabajo 8) — la API solo sirve JSON, PDF firmado y la
    interfaz explorable de DRF, así que una política restrictiva de
    "mismo origen por defecto" no rompe nada y cierra la puerta a XSS por
    inyección de script si algún dato sin sanear terminara en una
    respuesta HTML (por ejemplo, la vista explorable de DRF)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'",
        )
        return response
