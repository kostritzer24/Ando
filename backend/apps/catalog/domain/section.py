"""ADR-0001: el maestro guía solo aplica a secciones académicas; una
sección de taller no lleva maestro guía."""

from ..models import Section


class MaestroGuiaInvalido(Exception):
    pass


def validar_maestro_guia(tipo_seccion: str, homeroom_teacher) -> None:
    if tipo_seccion == Section.TIPO_TALLER and homeroom_teacher is not None:
        raise MaestroGuiaInvalido("Una sección de taller no puede tener maestro guía.")
