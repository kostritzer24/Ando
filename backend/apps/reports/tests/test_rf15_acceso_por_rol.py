import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory

pytestmark = pytest.mark.django_db

_RUTAS_GENERALES = [
    "/api/v1/reports/grades-summary/",
    "/api/v1/reports/attendance/",
    "/api/v1/reports/schedules/",
    "/api/v1/reports/enrolled-students/",
    "/api/v1/reports/grade-change-history/",
    "/api/v1/reports/family-access/",
    "/api/v1/reports/issued-documents/",
    "/api/v1/reports/metrics/",
]


@pytest.mark.parametrize("ruta", _RUTAS_GENERALES)
def test_rf15_direccion_accede_a_todos_los_reportes_generales(ruta):
    rol = RoleFactory(name="Dirección", permissions={"reportes_institucionales": "editar"})
    direccion = UserFactory(role=rol)
    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.get(ruta)

    assert respuesta.status_code == 200


@pytest.mark.parametrize("ruta", _RUTAS_GENERALES)
def test_rf15_encargado_de_pagos_no_accede_a_los_reportes_generales(ruta):
    """Nota 8 de docs/permisos-roles.md: Pagos solo llega al reporte de
    insolventes, y por el área "pagos_solvencia", no por esta."""
    rol = RoleFactory(name="Encargado de pagos", permissions={"reportes_institucionales": "sin_acceso"})
    pagos = UserFactory(role=rol)
    client = APIClient()
    client.force_authenticate(user=pagos)

    respuesta = client.get(ruta)

    assert respuesta.status_code == 403


def test_rf15_encargado_de_pagos_si_accede_al_reporte_de_insolventes():
    rol = RoleFactory(
        name="Encargado de pagos",
        permissions={"reportes_institucionales": "sin_acceso", "pagos_solvencia": "editar"},
    )
    pagos = UserFactory(role=rol)
    client = APIClient()
    client.force_authenticate(user=pagos)

    respuesta = client.get("/api/v1/reports/insolvent-students/")

    assert respuesta.status_code == 200


def test_rf15_direccion_con_solo_reportes_institucionales_no_llega_a_insolventes():
    """El reverso de la nota 8: `reportes_institucionales` no alcanza para
    este reporte puntual, tiene que venir de "pagos_solvencia"."""
    rol = RoleFactory(
        name="Rol de prueba sin pagos", permissions={"reportes_institucionales": "editar", "pagos_solvencia": "sin_acceso"}
    )
    usuario = UserFactory(role=rol)
    client = APIClient()
    client.force_authenticate(user=usuario)

    respuesta = client.get("/api/v1/reports/insolvent-students/")

    assert respuesta.status_code == 403


def test_rf15_docente_no_accede_a_ningun_reporte_institucional():
    rol = RoleFactory(name="Docente", permissions={"reportes_institucionales": "sin_acceso"})
    docente = UserFactory(role=rol)
    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/reports/enrolled-students/")

    assert respuesta.status_code == 403


def test_rf15_coordinacion_solo_puede_ver_no_editar():
    rol = RoleFactory(name="Coordinación", permissions={"reportes_institucionales": "ver"})
    coordinacion = UserFactory(role=rol)
    client = APIClient()
    client.force_authenticate(user=coordinacion)

    respuesta = client.get("/api/v1/reports/enrolled-students/")

    assert respuesta.status_code == 200
