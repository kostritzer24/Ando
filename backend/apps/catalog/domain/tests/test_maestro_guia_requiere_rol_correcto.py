"""HU-05 (Fase 5): el maestro guía siempre tiene el rol 'Docente con
sección a cargo', no cualquier usuario."""

import pytest

from apps.catalog.domain.section import MaestroGuiaInvalido, validar_maestro_guia
from apps.catalog.models import Section


class _RolFalso:
    def __init__(self, name):
        self.name = name


class _UsuarioFalso:
    def __init__(self, role_name):
        self.role = _RolFalso(role_name)


def test_maestro_guia_con_rol_correcto_es_valido():
    validar_maestro_guia(Section.TIPO_ACADEMICA, _UsuarioFalso("Docente con sección a cargo"))


def test_maestro_guia_con_rol_de_docente_comun_es_invalido():
    with pytest.raises(MaestroGuiaInvalido):
        validar_maestro_guia(Section.TIPO_ACADEMICA, _UsuarioFalso("Docente"))


def test_maestro_guia_con_rol_ajeno_es_invalido():
    with pytest.raises(MaestroGuiaInvalido):
        validar_maestro_guia(Section.TIPO_ACADEMICA, _UsuarioFalso("Tallerista"))
