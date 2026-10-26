from django.db.models import Q, QuerySet
from django.utils import timezone

from ..domain.announcement import (
    puede_administrar_aviso,
    validar_administracion,
    validar_publicacion,
)
from ..models import Announcement

ROL_DIRECCION = "Dirección"


def crear_aviso(*, published_by, audience, target_section=None, **datos) -> Announcement:
    validar_publicacion(
        audience=audience,
        target_section=target_section,
        audiencia_seccion=Announcement.AUDIENCIA_SECCION,
    )
    return Announcement.objects.create(
        published_by=published_by, audience=audience, target_section=target_section, **datos
    )


def puede_administrar(aviso: Announcement, usuario) -> bool:
    return puede_administrar_aviso(
        es_direccion=usuario.role.name == ROL_DIRECCION,
        es_autor=aviso.published_by_id == usuario.id,
    )


def _exigir_administracion(aviso: Announcement, usuario) -> None:
    validar_administracion(
        es_direccion=usuario.role.name == ROL_DIRECCION,
        es_autor=aviso.published_by_id == usuario.id,
    )


def actualizar_aviso(aviso: Announcement, *, usuario, cambios: dict) -> Announcement:
    """RN-18. La coherencia destinatario/sección se revisa con el resultado
    final: cambiar solo `audience` a "todos" deja de exigir la sección, pero
    no la borra sola."""
    _exigir_administracion(aviso, usuario)
    audience = cambios.get("audience", aviso.audience)
    target_section = cambios.get("target_section", aviso.target_section)
    validar_publicacion(
        audience=audience,
        target_section=target_section,
        audiencia_seccion=Announcement.AUDIENCIA_SECCION,
    )
    for campo, valor in cambios.items():
        setattr(aviso, campo, valor)
    aviso.save()
    return aviso


def retirar_aviso(aviso: Announcement, *, usuario) -> None:
    _exigir_administracion(aviso, usuario)
    aviso.is_active = False
    aviso.save(update_fields=["is_active", "updated_at"])


def avisos_vigentes(queryset: QuerySet) -> QuerySet:
    """HU-36: los vencidos dejan de mostrarse (no se borran, ver
    `Announcement.expires_at`)."""
    ahora = timezone.now()
    return queryset.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=ahora))
