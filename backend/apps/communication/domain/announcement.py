"""RF-13: un aviso es para todos o para una sección puntual, nunca las
dos cosas a la vez. RN-18: un docente solo edita y retira los avisos que
publicó; la dirección, cualquiera. Reglas puras, sin Django."""


class PublicacionDeAvisoInvalida(Exception):
    pass


class AvisoAjeno(Exception):
    pass


def validar_publicacion(*, audience: str, target_section, audiencia_seccion: str) -> None:
    if audience == audiencia_seccion and target_section is None:
        raise PublicacionDeAvisoInvalida("Un aviso dirigido a una sección necesita elegir cuál.")
    if audience != audiencia_seccion and target_section is not None:
        raise PublicacionDeAvisoInvalida("Un aviso para 'todos' no lleva una sección.")


def puede_administrar_aviso(*, es_direccion: bool, es_autor: bool) -> bool:
    return es_direccion or es_autor


def validar_administracion(*, es_direccion: bool, es_autor: bool) -> None:
    if not puede_administrar_aviso(es_direccion=es_direccion, es_autor=es_autor):
        raise AvisoAjeno("Solo puedes editar o retirar los avisos que tú publicaste.")
