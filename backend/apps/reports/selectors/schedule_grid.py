"""Horario en cuadrícula (días × períodos) de una sección o de una persona.
Es el mismo horario que arma Dirección en `/schedule-blocks/`, ordenado
como se cuelga en la pared: una fila por período, una columna por día."""

from apps.accounts.models import User
from apps.catalog.models import Section
from apps.scheduling.domain.day_structure import HORARIO_PERIODOS, PERIODOS_TALLER
from apps.scheduling.models import ScheduleBlock

DIAS = [
    (ScheduleBlock.LUNES, "Lunes"),
    (ScheduleBlock.MARTES, "Martes"),
    (ScheduleBlock.MIERCOLES, "Miércoles"),
    (ScheduleBlock.JUEVES, "Jueves"),
    (ScheduleBlock.VIERNES, "Viernes"),
]
RECESO = {"inicio": "10:00", "fin": "10:40"}


class SujetoNoEncontrado(Exception):
    pass


def _hora(valor) -> str:
    return valor.strftime("%H:%M")


def horario_en_cuadricula(*, section_id: str | None = None, teacher_id: str | None = None) -> dict:
    """Devuelve `{titulo, subtitulo, dias, periodos}`; cada período trae sus
    celdas por día (`curso` y `detalle`: el docente cuando se mira una
    sección, la sección cuando se mira a una persona)."""
    bloques = ScheduleBlock.objects.filter(
        is_active=True, assignment__is_active=True
    ).select_related("assignment__course", "assignment__section", "assignment__teacher")

    if section_id:
        seccion = Section.objects.filter(public_id=section_id).select_related("cycle").first()
        if seccion is None:
            raise SujetoNoEncontrado("No se encontró la sección.")
        bloques = bloques.filter(assignment__section=seccion)
        titulo = f"Horario de {seccion}"
        subtitulo = f"Ciclo {seccion.cycle.year}"
        detalle = lambda b: b.assignment.teacher.nombre_completo()  # noqa: E731
    elif teacher_id:
        persona = User.objects.filter(public_id=teacher_id).first()
        if persona is None:
            raise SujetoNoEncontrado("No se encontró a la persona.")
        bloques = bloques.filter(assignment__teacher=persona)
        titulo = f"Horario de {persona.nombre_completo()}"
        subtitulo = persona.role.name
        detalle = lambda b: f"{b.assignment.section} ({b.assignment.cycle.year})"  # noqa: E731
    else:
        raise SujetoNoEncontrado("Indica una sección o una persona.")

    bloques = list(bloques)
    hay_tarde = any(b.period_number in PERIODOS_TALLER for b in bloques)
    hay_manana = any(b.period_number not in PERIODOS_TALLER for b in bloques)
    numeros = [n for n in sorted(HORARIO_PERIODOS) if n not in PERIODOS_TALLER]
    if hay_tarde and not hay_manana:
        numeros = []
    if hay_tarde:
        numeros += list(PERIODOS_TALLER)

    celdas = {(b.day_of_week, b.period_number): b for b in bloques}
    periodos = []
    for numero in numeros:
        inicio, fin = HORARIO_PERIODOS[numero]
        fila = {
            "numero": numero,
            "inicio": _hora(inicio),
            "fin": _hora(fin),
            "receso_antes": numero == 4,
            "celdas": {},
        }
        for dia, _etiqueta in DIAS:
            bloque = celdas.get((dia, numero))
            fila["celdas"][dia] = (
                {"curso": bloque.assignment.course.name, "detalle": detalle(bloque)}
                if bloque
                else None
            )
        periodos.append(fila)

    return {
        "titulo": titulo,
        "subtitulo": subtitulo,
        "dias": [{"clave": c, "etiqueta": e} for c, e in DIAS],
        "receso": RECESO,
        "periodos": periodos,
    }
