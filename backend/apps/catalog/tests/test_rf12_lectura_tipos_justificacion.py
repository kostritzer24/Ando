import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import JustificationType


@pytest.mark.django_db
def test_un_docente_puede_listar_tipos_de_justificacion_para_elegir_uno():
    """RF-12: cualquier rol que registra una justificación de falta
    necesita elegir su tipo, aunque "Datos maestros" le dé sin_acceso
    (docs/permisos-roles.md) — ver JustificationTypeViewSet."""
    JustificationType.objects.create(name="Constancia médica", requires_document=True)
    rol = RoleFactory(
        name="Docente", permissions={"datos_maestros": "sin_acceso", "asistencia": "editar"}
    )
    docente = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/justification-types/")

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 1


@pytest.mark.django_db
def test_un_docente_no_puede_crear_ni_editar_tipos_de_justificacion():
    """Leer pasa por "asistencia", pero administrar el catálogo sigue
    siendo exclusivo de "datos_maestros"."""
    rol = RoleFactory(
        name="Docente", permissions={"datos_maestros": "sin_acceso", "asistencia": "editar"}
    )
    docente = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post("/api/v1/justification-types/", {"name": "Otro tipo"}, format="json")

    assert respuesta.status_code == 403
