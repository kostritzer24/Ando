"""RF-13: un aviso es para todos o para una sección puntual, nunca las
dos cosas a la vez. Regla pura, sin Django."""


class PublicacionDeAvisoInvalida(Exception):
    pass


def validar_publicacion(*, audience: str, target_section, audiencia_seccion: str) -> None:
    if audience == audiencia_seccion and target_section is None:
        raise PublicacionDeAvisoInvalida("Un aviso dirigido a una sección necesita elegir cuál.")
    if audience != audiencia_seccion and target_section is not None:
        raise PublicacionDeAvisoInvalida("Un aviso para 'todos' no lleva una sección.")
