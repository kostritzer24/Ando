"""ADR-0001: el docente a cargo solo aplica a secciones académicas; una
sección de taller no lo lleva. Además (HU-05, Fase 5), siempre es un
usuario con rol "Docente" — no cualquier usuario. Ya no existe un rol
aparte de "maestro guía": cualquier docente puede estar a cargo."""

from ..models import Section

ROL_MAESTRO_GUIA = "Docente"


class MaestroGuiaInvalido(Exception):
    pass


def validar_maestro_guia(tipo_seccion: str, homeroom_teacher) -> None:
    if tipo_seccion == Section.TIPO_TALLER and homeroom_teacher is not None:
        raise MaestroGuiaInvalido("Una sección de taller no puede tener docente a cargo.")

    if homeroom_teacher is not None and homeroom_teacher.role.name != ROL_MAESTRO_GUIA:
        raise MaestroGuiaInvalido(f"El docente a cargo debe tener el rol '{ROL_MAESTRO_GUIA}'.")
