from django.db.models import Q, QuerySet
from django.utils import timezone

from ..domain.announcement import validar_publicacion
from ..models import Announcement


def crear_aviso(*, published_by, audience, target_section=None, **datos) -> Announcement:
    validar_publicacion(
        audience=audience,
        target_section=target_section,
        audiencia_seccion=Announcement.AUDIENCIA_SECCION,
    )
    return Announcement.objects.create(
        published_by=published_by, audience=audience, target_section=target_section, **datos
    )


def avisos_vigentes(queryset: QuerySet) -> QuerySet:
    """HU-36: los vencidos dejan de mostrarse (no se borran, ver
    `Announcement.expires_at`)."""
    ahora = timezone.now()
    return queryset.filter(Q(expires_at__isnull=True) | Q(expires_at__gt=ahora))
