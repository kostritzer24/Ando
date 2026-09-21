import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.core.models import AuditLog
from apps.core.services import registrar_acceso, registrar_cambio


@pytest.mark.django_db
def test_direccion_consulta_la_bitacora_de_cambios():
    rol_direccion = RoleFactory(name="Dirección", permissions={"bitacora_registro_acceso": "ver"})
    direccion = UserFactory(role=rol_direccion)
    autor = UserFactory()
    registrar_cambio(
        usuario=autor,
        entidad_nombre="grading.Grade",
        entidad_id=7,
        accion=AuditLog.ACCION_ACTUALIZAR,
        valor_anterior={"punteo_real": 60},
        valor_nuevo={"punteo_real": 65},
    )

    client = APIClient()
    client.force_authenticate(user=direccion)
    respuesta = client.get("/api/v1/audit-log/?entity=grading.Grade")

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 1
    assert respuesta.data["results"][0]["entity_name"] == "grading.Grade"


@pytest.mark.django_db
def test_docente_no_puede_consultar_la_bitacora_acceso_no_autorizado():
    rol_docente = RoleFactory(
        name="Docente", permissions={"bitacora_registro_acceso": "sin_acceso"}
    )
    docente = UserFactory(role=rol_docente)

    client = APIClient()
    client.force_authenticate(user=docente)
    respuesta = client.get("/api/v1/audit-log/")

    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_direccion_consulta_el_registro_de_accesos():
    rol_direccion = RoleFactory(name="Dirección", permissions={"bitacora_registro_acceso": "ver"})
    direccion = UserFactory(role=rol_direccion)
    otro_usuario = UserFactory()
    registrar_acceso(usuario=otro_usuario, pantalla="/api/v1/roles/")

    client = APIClient()
    client.force_authenticate(user=direccion)
    respuesta = client.get(f"/api/v1/access-log/?user={otro_usuario.public_id}")

    assert respuesta.status_code == 200
    assert respuesta.data["count"] >= 1
