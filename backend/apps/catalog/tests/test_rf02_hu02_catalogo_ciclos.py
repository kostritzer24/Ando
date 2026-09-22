import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import SchoolCycle

from .factories import SchoolCycleFactory


@pytest.mark.django_db
def test_rf02_direccion_crea_un_ciclo_escolar():
    rol = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar"})
    direccion = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/cycles/",
        {"year": 2027, "start_date": "2027-01-11", "end_date": "2027-10-29"},
        format="json",
    )

    assert respuesta.status_code == 201
    assert SchoolCycle.objects.filter(year=2027).exists()


@pytest.mark.django_db
def test_rf02_coordinacion_ve_pero_no_puede_crear_ciclos():
    rol = RoleFactory(name="Coordinación", permissions={"datos_maestros": "ver"})
    coordinacion = UserFactory(role=rol)
    SchoolCycleFactory(year=2026)

    client = APIClient()
    client.force_authenticate(user=coordinacion)

    respuesta_listar = client.get("/api/v1/cycles/")
    assert respuesta_listar.status_code == 200
    assert respuesta_listar.data["count"] == 1

    respuesta_crear = client.post(
        "/api/v1/cycles/",
        {"year": 2028, "start_date": "2028-01-10", "end_date": "2028-10-27"},
        format="json",
    )
    assert respuesta_crear.status_code == 403


@pytest.mark.django_db
def test_rf02_docente_no_tiene_acceso_a_datos_maestros_acceso_no_autorizado():
    """Caso de acceso no autorizado (sección 16)."""
    rol = RoleFactory(name="Docente", permissions={"datos_maestros": "sin_acceso"})
    docente = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/cycles/")
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_rf02_usuario_no_autenticado_no_ve_datos_maestros():
    client = APIClient()
    respuesta = client.get("/api/v1/cycles/")
    assert respuesta.status_code in (401, 403)


@pytest.mark.django_db
def test_hu02_borrar_un_ciclo_es_baja_logica_no_borrado():
    rol = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar"})
    direccion = UserFactory(role=rol)
    ciclo = SchoolCycleFactory(year=2026)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.delete(f"/api/v1/cycles/{ciclo.public_id}/")

    assert respuesta.status_code == 204
    ciclo.refresh_from_db()
    assert ciclo.is_active is False
    assert SchoolCycle.objects.filter(pk=ciclo.pk).exists()
