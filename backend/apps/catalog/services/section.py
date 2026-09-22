from ..domain.section import validar_maestro_guia
from ..models import SchoolCycle, Section


def crear_seccion(
    *, cycle: SchoolCycle, grade: str, letter: str, type: str, homeroom_teacher=None
) -> Section:
    validar_maestro_guia(type, homeroom_teacher)
    return Section.objects.create(
        cycle=cycle, grade=grade, letter=letter, type=type, homeroom_teacher=homeroom_teacher
    )


def actualizar_seccion(
    seccion: Section, *, grade: str, letter: str, type: str, homeroom_teacher=None
) -> Section:
    validar_maestro_guia(type, homeroom_teacher)
    seccion.grade = grade
    seccion.letter = letter
    seccion.type = type
    seccion.homeroom_teacher = homeroom_teacher
    seccion.save(update_fields=["grade", "letter", "type", "homeroom_teacher", "updated_at"])
    return seccion
