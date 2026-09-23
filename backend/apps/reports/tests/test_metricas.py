import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.attendance.tests.factories import AttendanceFactory
from apps.core.services import registrar_acceso

pytestmark = pytest.mark.django_db


def _direccion():
    rol = RoleFactory(name="Dirección", permissions={"reportes_institucionales": "editar"})
    return UserFactory(role=rol)


def test_metricas_no_exponen_datos_personales():
    client = APIClient()
    client.force_authenticate(user=_direccion())

    respuesta = client.get("/api/v1/reports/metrics/")

    assert respuesta.status_code == 200
    claves = set(respuesta.data.keys())
    assert claves == {
        "period_start",
        "period_end",
        "administrative_processes_percentage",
        "guardians_portal_usage_percentage",
    }


def test_metricas_cuenta_procesos_con_actividad_esta_semana():
    AttendanceFactory()  # deja "asistencia" con al menos un registro.

    client = APIClient()
    client.force_authenticate(user=_direccion())
    respuesta = client.get("/api/v1/reports/metrics/")

    # 1 de 6 categorías con actividad = 17 % (redondeado).
    assert respuesta.data["administrative_processes_percentage"] >= 17


def test_metricas_porcentaje_de_encargados_que_consultan_el_portal():
    rol_familia = RoleFactory(name="Padre de familia", permissions={})
    con_acceso = UserFactory(role=rol_familia, username="con.acceso")
    UserFactory(role=rol_familia, username="sin.acceso")
    registrar_acceso(usuario=con_acceso, pantalla="/portal")

    client = APIClient()
    client.force_authenticate(user=_direccion())
    respuesta = client.get("/api/v1/reports/metrics/")

    assert respuesta.data["guardians_portal_usage_percentage"] == 50
