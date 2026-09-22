"""RN-17: cada docente edita solo las asignaciones (eventos) que publicó;
Dirección puede editar todo el calendario."""


class PublicacionInvalida(Exception):
    pass


def validar_creacion(
    *, event_type: str, tipo_institucional: str, is_direccion: bool, assignment, published_by
) -> None:
    if event_type == tipo_institucional and not is_direccion:
        raise PublicacionInvalida(
            "Solo Dirección puede publicar avisos institucionales en el calendario."
        )
    if assignment is not None and not is_direccion and assignment.teacher_id != published_by.id:
        raise PublicacionInvalida(
            "Solo podés publicar en el calendario asignaciones que son tuyas."
        )


def puede_editar(*, is_direccion: bool, published_by_id: int, user_id: int) -> bool:
    return is_direccion or published_by_id == user_id
