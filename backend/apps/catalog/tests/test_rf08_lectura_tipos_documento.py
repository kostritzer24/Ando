import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import DocumentType


@pytest.mark.django_db
def test_rf08_quien_emite_documentos_puede_listar_los_tipos_sin_datos_maestros():
    """Hallazgo A-005: la pantalla de documentos de Encargado de pagos
    fallaba entera por un 403 en /document-types/."""
    DocumentType.objects.create(name="Constancia de solvencia")
    rol = RoleFactory(
        name="Encargado de pagos",
        permissions={"datos_maestros": "sin_acceso", "documentos": "editar"},
    )
    client = APIClient()
    client.force_authenticate(user=UserFactory(role=rol))

    assert client.get("/api/v1/document-types/").status_code == 200


@pytest.mark.django_db
def test_rf08_quien_emite_documentos_no_administra_el_catalogo_de_tipos():
    rol = RoleFactory(
        name="Encargado de pagos",
        permissions={"datos_maestros": "sin_acceso", "documentos": "editar"},
    )
    client = APIClient()
    client.force_authenticate(user=UserFactory(role=rol))

    respuesta = client.post("/api/v1/document-types/", {"name": "Otro"}, format="json")

    assert respuesta.status_code == 403
