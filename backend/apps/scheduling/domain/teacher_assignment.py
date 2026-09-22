"""ADR-0001: una asignación docente solo es válida si el tipo del curso
coincide con el tipo de la sección (académico↔académica,
taller↔taller), y RF-05 distingue explícitamente "asignar docentes a
cursos, talleristas a talleres": el rol de quien se asigna tiene que
corresponder al tipo de curso."""

ROLES_VALIDOS_POR_TIPO_CURSO = {
    "academico": {"Docente", "Docente con sección a cargo"},
    "taller": {"Tallerista"},
}


class AsignacionInvalida(Exception):
    pass


def validar_asignacion(*, course_type: str, section_type: str, teacher_role_name: str) -> None:
    tipo_esperado_seccion = "academica" if course_type == "academico" else "taller"
    if section_type != tipo_esperado_seccion:
        raise AsignacionInvalida(
            f"Un curso de tipo '{course_type}' no se puede asignar "
            f"a una sección de tipo '{section_type}'."
        )

    roles_validos = ROLES_VALIDOS_POR_TIPO_CURSO.get(course_type, set())
    if teacher_role_name not in roles_validos:
        raise AsignacionInvalida(
            f"El rol '{teacher_role_name}' no puede asignarse a un curso de tipo '{course_type}'."
        )
