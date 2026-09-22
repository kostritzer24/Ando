"""ADR-0001: el maestro guía solo aplica a secciones académicas; una
sección de taller no lleva maestro guía. Además (HU-05, Fase 5), el
maestro guía siempre es un docente con rol "Docente con sección a
cargo" — no cualquier usuario."""

from ..models import Section

ROL_MAESTRO_GUIA = "Docente con sección a cargo"


class MaestroGuiaInvalido(Exception):
    pass


def validar_maestro_guia(tipo_seccion: str, homeroom_teacher) -> None:
    if tipo_seccion == Section.TIPO_TALLER and homeroom_teacher is not None:
        raise MaestroGuiaInvalido("Una sección de taller no puede tener maestro guía.")

    if homeroom_teacher is not None and homeroom_teacher.role.name != ROL_MAESTRO_GUIA:
        raise MaestroGuiaInvalido(f"El maestro guía debe tener el rol '{ROL_MAESTRO_GUIA}'.")
