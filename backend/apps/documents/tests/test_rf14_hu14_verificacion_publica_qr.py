import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import DocumentTypeFactory
from apps.documents.models import IssuedDocument
from apps.students.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


def _emitir_documento():
    tipo = DocumentTypeFactory(name="Constancia de estudio", template_key="constancia_estudio")
    inscripcion = EnrollmentFactory()
    rol = RoleFactory(name="Dirección", permissions={"documentos": "editar"})
    direccion = UserFactory(role=rol)
    client = APIClient()
    client.force_authenticate(user=direccion)
    client.post(
        "/api/v1/documents/issue/",
        {"enrollment": str(inscripcion.public_id), "document_type": str(tipo.public_id)},
    )
    return IssuedDocument.objects.get(enrollment=inscripcion)


def test_rf14_verificar_un_codigo_valido_sin_sesion_devuelve_solo_lo_minimo():
    documento = _emitir_documento()

    client = APIClient()  # sin autenticar — HU-14: la única ruta pública.
    respuesta = client.get(f"/api/v1/verify/{documento.verification_code}/")

    assert respuesta.status_code == 200
    assert set(respuesta.data.keys()) == {"tipo_documento", "fecha", "estudiante"}
    assert respuesta.data["estudiante"] == documento.enrollment.student.nombre_completo()


def test_rf14_un_codigo_inexistente_indica_que_el_documento_no_es_valido():
    client = APIClient()
    respuesta = client.get("/api/v1/verify/000000000000/")
    assert respuesta.status_code == 404


def test_rf14_un_documento_dado_de_baja_deja_de_verificarse():
    documento = _emitir_documento()
    documento.is_active = False
    documento.save(update_fields=["is_active"])

    client = APIClient()
    respuesta = client.get(f"/api/v1/verify/{documento.verification_code}/")

    assert respuesta.status_code == 404
