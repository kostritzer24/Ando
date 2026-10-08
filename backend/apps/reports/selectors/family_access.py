"""RF-15/RNF-07, reporte 7: accesos de las familias al portal público."""

from apps.core.domain.pantallas import nombre_de_pantalla
from apps.core.models import AccessLog

ROL_FAMILIA = "Padre de familia"


def accesos_de_familias() -> list[dict]:
    accesos = AccessLog.objects.filter(user__role__name=ROL_FAMILIA).select_related("user")
    return [
        {
            "user": acceso.user.username,
            "screen_viewed": nombre_de_pantalla(acceso.screen_viewed),
            "accessed_at": acceso.accessed_at,
        }
        for acceso in accesos.order_by("-accessed_at")
    ]
