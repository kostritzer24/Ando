import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import ActivityType

from .factories import GradingUnitFactory, SchoolCycleFactory


@pytest.mark.django_db
def test_un_docente_puede_listar_las_unidades_de_un_ciclo_para_diseñar_su_unidad():
    """RF-17: un docente necesita elegir la unidad al diseñarla, aunque
    "datos_maestros" le dé sin_acceso (ver GradingUnitViewSet) — conoce
    el ciclo por su propia asignación."""
    ciclo = SchoolCycleFactory()
    GradingUnitFactory(cycle=ciclo, number=1)
    rol = RoleFactory(
        name="Docente", permissions={"datos_maestros": "sin_acceso", "notas": "editar"}
    )
    docente = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get(f"/api/v1/cycles/{ciclo.public_id}/units/")

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 1


@pytest.mark.django_db
def test_un_docente_no_puede_crear_ni_editar_unidades():
    ciclo = SchoolCycleFactory()
    rol = RoleFactory(
        name="Docente", permissions={"datos_maestros": "sin_acceso", "notas": "editar"}
    )
    docente = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        f"/api/v1/cycles/{ciclo.public_id}/units/",
        {"number": 1, "start_date": "2026-01-12", "end_date": "2026-02-28"},
        format="json",
    )

    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_un_docente_puede_listar_los_tipos_de_actividad_para_diseñar_su_unidad():
    ActivityType.objects.create(name="Prueba corta", counts_as_short_quiz=True)
    rol = RoleFactory(
        name="Docente", permissions={"datos_maestros": "sin_acceso", "notas": "editar"}
    )
    docente = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/activity-types/")

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 1


@pytest.mark.django_db
def test_un_docente_no_puede_crear_ni_editar_tipos_de_actividad():
    rol = RoleFactory(
        name="Docente", permissions={"datos_maestros": "sin_acceso", "notas": "editar"}
    )
    docente = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post("/api/v1/activity-types/", {"name": "Otro tipo"}, format="json")

    assert respuesta.status_code == 403
