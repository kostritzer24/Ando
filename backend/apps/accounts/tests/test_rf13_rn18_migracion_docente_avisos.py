import importlib

import pytest
from django.apps import apps as django_apps

from apps.accounts.tests.factories import RoleFactory

pytestmark = pytest.mark.django_db

migracion = importlib.import_module("apps.accounts.migrations.0004_docente_publica_avisos")


def test_rf13_la_migracion_da_edicion_de_avisos_al_docente_ya_sembrado():
    """En producción el rol ya existe con `avisos: ver`; la migración lo
    sube a `editar` sin tocar las demás áreas."""
    docente = RoleFactory(name="Docente", permissions={"avisos": "ver", "notas": "editar"})

    migracion.docente_publica_avisos(django_apps, None)

    docente.refresh_from_db()
    assert docente.permissions == {"avisos": "editar", "notas": "editar"}


def test_rf13_revertir_la_migracion_devuelve_al_docente_a_solo_ver():
    docente = RoleFactory(name="Docente", permissions={"avisos": "editar"})

    migracion.docente_solo_ve_avisos(django_apps, None)

    docente.refresh_from_db()
    assert docente.permissions["avisos"] == "ver"
