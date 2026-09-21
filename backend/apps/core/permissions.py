"""
Permisos reutilizables. La clase base de DRF (settings.REST_FRAMEWORK,
DEFAULT_PERMISSION_CLASSES) ya niega todo por defecto con `DenyAll` —
cada vista concede explícitamente con `PermisoPorArea`, conforme a la
sección 14.2 del prompt maestro y a docs/permisos-roles.md.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

SIN_ACCESO = "sin_acceso"
VER = "ver"
EDITAR = "editar"

_RANGO = {SIN_ACCESO: 0, VER: 1, EDITAR: 2}


class DenyAll(BasePermission):
    """Permiso por defecto de todo el proyecto: niega siempre. Ningún
    endpoint queda abierto por omisión (sección 14.2)."""

    def has_permission(self, request, view) -> bool:
        return False


class PermisoPorArea(BasePermission):
    """
    Compara el nivel que el rol del usuario tiene en `view.area` (una de
    las áreas de docs/permisos-roles.md) contra el nivel que pide el
    método HTTP. GET/HEAD/OPTIONS piden `ver`; el resto pide `editar`,
    salvo que la vista declare `nivel_requerido(request)` con una regla
    distinta.

    Esta clase resuelve el permiso por ROL. El alcance por OBJETO (un
    encargado solo ve a sus estudiantes, un docente solo sus cursos) es
    responsabilidad aparte de `ScopedQuerysetMixin` — nunca se resuelve
    comparando un identificador de la URL contra el usuario.
    """

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.must_change_password:
            # Contraseña temporal sin cambiar todavía (sección 14.1): solo
            # /auth/change-password/ y /auth/logout/ quedan disponibles,
            # y ninguna de las dos usa PermisoPorArea.
            return False
        area = getattr(view, "area", None)
        if not area:
            raise ValueError(
                f"{view.__class__.__name__} usa PermisoPorArea pero no declaró `area`."
            )
        if hasattr(view, "nivel_requerido"):
            nivel_pedido = view.nivel_requerido(request)
        else:
            nivel_pedido = VER if request.method in SAFE_METHODS else EDITAR
        nivel_usuario = request.user.role.nivel_en(area)
        return _RANGO[nivel_usuario] >= _RANGO[nivel_pedido]
