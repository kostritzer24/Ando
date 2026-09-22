import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory

from .factories import StudentFactory


@pytest.mark.django_db
def test_direccion_puede_leer_y_editar_datos_sensibles():
    rol = RoleFactory(
        name="Dirección",
        permissions={"estudiantes_encargados": "editar", "datos_sensibles": "editar"},
    )
    direccion = UserFactory(role=rol)
    estudiante = StudentFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta_lectura = client.get(f"/api/v1/students/{estudiante.public_id}/sensitive/")
    assert respuesta_lectura.status_code == 200

    respuesta_escritura = client.patch(
        f"/api/v1/students/{estudiante.public_id}/sensitive/",
        {"health_notes": "Alergia a la penicilina."},
        format="json",
    )
    assert respuesta_escritura.status_code == 200
    estudiante.refresh_from_db()
    assert estudiante.health_notes == "Alergia a la penicilina."


@pytest.mark.django_db
def test_administrador_puede_leer_pero_no_editar_datos_sensibles():
    """Confirmado en el cierre de la Fase 1: Administrador ve (no
    edita) los datos sensibles — docs/permisos-roles.md, nota 9."""
    rol = RoleFactory(
        name="Administrador del sistema",
        permissions={"estudiantes_encargados": "ver", "datos_sensibles": "ver"},
    )
    admin = UserFactory(role=rol)
    estudiante = StudentFactory()

    client = APIClient()
    client.force_authenticate(user=admin)

    respuesta_lectura = client.get(f"/api/v1/students/{estudiante.public_id}/sensitive/")
    assert respuesta_lectura.status_code == 200

    respuesta_escritura = client.patch(
        f"/api/v1/students/{estudiante.public_id}/sensitive/",
        {"health_notes": "No debería poder escribir esto."},
        format="json",
    )
    assert respuesta_escritura.status_code == 403


@pytest.mark.django_db
def test_docente_no_alcanza_los_datos_sensibles_acceso_no_autorizado():
    rol = RoleFactory(
        name="Docente",
        permissions={"estudiantes_encargados": "ver", "datos_sensibles": "sin_acceso"},
    )
    docente = UserFactory(role=rol)
    estudiante = StudentFactory()

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get(f"/api/v1/students/{estudiante.public_id}/sensitive/")
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_padre_de_familia_no_alcanza_los_datos_sensibles_de_su_propio_hijo():
    """RNF-04: ni siquiera la familia ve los datos sensibles — quedan
    reservados a Dirección."""
    rol = RoleFactory(
        name="Padre de familia",
        permissions={"estudiantes_encargados": "ver", "datos_sensibles": "sin_acceso"},
    )
    encargado_usuario = UserFactory(role=rol)
    estudiante = StudentFactory()

    client = APIClient()
    client.force_authenticate(user=encargado_usuario)

    respuesta = client.get(f"/api/v1/students/{estudiante.public_id}/sensitive/")
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_serializer_general_nunca_incluye_datos_sensibles():
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)
    estudiante = StudentFactory(health_notes="Dato sensible que no debe salir aquí.")

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.get(f"/api/v1/students/{estudiante.public_id}/")

    assert respuesta.status_code == 200
    assert "health_notes" not in respuesta.data
    assert "socioeconomic_notes" not in respuesta.data
