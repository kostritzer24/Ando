import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.scheduling.models import ScheduleBlock

from .factories import TeacherAssignmentFactory


@pytest.mark.django_db
def test_rf26_docente_consulta_su_propio_horario():
    rol = RoleFactory(name="Docente", permissions={"horarios_calendario": "ver"})
    docente = UserFactory(role=rol)
    asignacion = TeacherAssignmentFactory(teacher=docente)
    ScheduleBlock.objects.create(assignment=asignacion, day_of_week="lunes", period_number=1)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/schedule/mine/")

    assert respuesta.status_code == 200
    assert len(respuesta.data) == 1
    assert respuesta.data[0]["day_of_week"] == "lunes"


@pytest.mark.django_db
def test_rf26_no_incluye_horario_de_otro_docente():
    rol = RoleFactory(name="Docente", permissions={"horarios_calendario": "ver"})
    docente = UserFactory(role=rol)
    asignacion_ajena = TeacherAssignmentFactory()
    ScheduleBlock.objects.create(assignment=asignacion_ajena, day_of_week="lunes", period_number=1)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/schedule/mine/")

    assert respuesta.data == []


@pytest.mark.django_db
def test_direccion_no_usa_este_endpoint_acceso_no_autorizado():
    """`/schedule/mine/` es para docentes, maestros guía y talleristas
    (`docs/api.md`) — Dirección tiene su propia vista de todo el
    horario en `/schedule-blocks/`."""
    rol = RoleFactory(name="Dirección", permissions={"horarios_calendario": "editar"})
    direccion = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.get("/api/v1/schedule/mine/")

    assert respuesta.status_code == 403
