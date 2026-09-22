import pytest

from apps.scheduling.domain.calendar_event import (
    PublicacionInvalida,
    puede_editar,
    validar_creacion,
)

TIPO_INSTITUCIONAL = "institucional"
TIPO_ASIGNACION_DOCENTE = "asignacion_docente"


class _UsuarioFalso:
    def __init__(self, id):
        self.id = id


class _AsignacionFalsa:
    def __init__(self, teacher_id):
        self.teacher_id = teacher_id


def test_direccion_puede_publicar_un_evento_institucional():
    direccion = _UsuarioFalso(id=1)
    validar_creacion(
        event_type=TIPO_INSTITUCIONAL,
        tipo_institucional=TIPO_INSTITUCIONAL,
        is_direccion=True,
        assignment=None,
        published_by=direccion,
    )


def test_docente_no_puede_publicar_un_evento_institucional():
    docente = _UsuarioFalso(id=2)
    with pytest.raises(PublicacionInvalida):
        validar_creacion(
            event_type=TIPO_INSTITUCIONAL,
            tipo_institucional=TIPO_INSTITUCIONAL,
            is_direccion=False,
            assignment=None,
            published_by=docente,
        )


def test_docente_puede_publicar_su_propia_asignacion():
    docente = _UsuarioFalso(id=2)
    su_asignacion = _AsignacionFalsa(teacher_id=2)
    validar_creacion(
        event_type=TIPO_ASIGNACION_DOCENTE,
        tipo_institucional=TIPO_INSTITUCIONAL,
        is_direccion=False,
        assignment=su_asignacion,
        published_by=docente,
    )


def test_docente_no_puede_publicar_una_asignacion_ajena():
    docente = _UsuarioFalso(id=2)
    asignacion_ajena = _AsignacionFalsa(teacher_id=99)
    with pytest.raises(PublicacionInvalida):
        validar_creacion(
            event_type=TIPO_ASIGNACION_DOCENTE,
            tipo_institucional=TIPO_INSTITUCIONAL,
            is_direccion=False,
            assignment=asignacion_ajena,
            published_by=docente,
        )


def test_direccion_puede_publicar_cualquier_asignacion():
    direccion = _UsuarioFalso(id=1)
    asignacion_ajena = _AsignacionFalsa(teacher_id=99)
    validar_creacion(
        event_type=TIPO_ASIGNACION_DOCENTE,
        tipo_institucional=TIPO_INSTITUCIONAL,
        is_direccion=True,
        assignment=asignacion_ajena,
        published_by=direccion,
    )


def test_rn17_direccion_puede_editar_cualquier_evento():
    assert puede_editar(is_direccion=True, published_by_id=99, user_id=1) is True


def test_rn17_docente_edita_solo_lo_que_publico():
    assert puede_editar(is_direccion=False, published_by_id=2, user_id=2) is True
    assert puede_editar(is_direccion=False, published_by_id=99, user_id=2) is False
