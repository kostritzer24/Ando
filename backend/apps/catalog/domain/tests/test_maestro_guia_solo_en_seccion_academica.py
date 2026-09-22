"""ADR-0001: el maestro guía solo aplica a secciones académicas."""

import pytest

from apps.catalog.domain.section import MaestroGuiaInvalido, validar_maestro_guia
from apps.catalog.models import Section


class _MaestroGuiaFalso:
    role = type("Rol", (), {"name": "Docente con sección a cargo"})()


def test_seccion_taller_con_maestro_guia_es_invalida():
    with pytest.raises(MaestroGuiaInvalido):
        validar_maestro_guia(Section.TIPO_TALLER, homeroom_teacher=_MaestroGuiaFalso())


def test_seccion_taller_sin_maestro_guia_es_valida():
    validar_maestro_guia(Section.TIPO_TALLER, homeroom_teacher=None)


def test_seccion_academica_con_maestro_guia_es_valida():
    validar_maestro_guia(Section.TIPO_ACADEMICA, homeroom_teacher=_MaestroGuiaFalso())


def test_seccion_academica_sin_maestro_guia_es_valida():
    validar_maestro_guia(Section.TIPO_ACADEMICA, homeroom_teacher=None)
