from apps.core.services import registrar_acceso


class RegistraAccesoMixin:
    """Registra en AccessLog cada petición autenticada que llega a la
    vista (RNF-07). Se aplica en `initial()`, que en DRF corre después de
    `perform_authentication()`, así que `request.user` ya está resuelto."""

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user and request.user.is_authenticated:
            registrar_acceso(usuario=request.user, pantalla=request.path)


class ScopedQuerysetMixin:
    """
    Obliga a que el queryset de cualquier vista de listado/detalle se
    filtre a partir del usuario autenticado, nunca comparando el id que
    viene en la URL contra el usuario (sección 14.2 del prompt maestro:
    "si el filtro se hace mal, cambiar un número en la barra de
    direcciones expone el expediente de otro menor").

    Cada vista que mezcla este mixin implementa `scope_queryset`.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.scope_queryset(queryset, self.request.user)

    def scope_queryset(self, queryset, user):
        raise NotImplementedError(f"{self.__class__.__name__} debe implementar scope_queryset().")
