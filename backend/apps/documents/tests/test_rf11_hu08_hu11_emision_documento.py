import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import DocumentTypeFactory
from apps.documents.models import IssuedDocument
from apps.students.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


def _direccion():
    rol = RoleFactory(name="Dirección", permissions={"documentos": "editar"})
    return UserFactory(role=rol)


def test_rf11_direccion_emite_una_constancia_de_estudio():
    tipo = DocumentTypeFactory(name="Constancia de estudio", template_key="constancia_estudio")
    inscripcion = EnrollmentFactory()
    client = APIClient()
    client.force_authenticate(user=_direccion())

    respuesta = client.post(
        "/api/v1/documents/issue/",
        {"enrollment": str(inscripcion.public_id), "document_type": str(tipo.public_id)},
    )

    assert respuesta.status_code == 200
    assert respuesta.content[:4] == b"%PDF"
    documento = IssuedDocument.objects.get(enrollment=inscripcion)
    assert documento.document_type == tipo


def test_rf11_carta_membretada_necesita_texto():
    tipo = DocumentTypeFactory(name="Carta membretada", template_key="carta_membretada")
    inscripcion = EnrollmentFactory()
    client = APIClient()
    client.force_authenticate(user=_direccion())

    respuesta = client.post(
        "/api/v1/documents/issue/",
        {"enrollment": str(inscripcion.public_id), "document_type": str(tipo.public_id)},
    )

    assert respuesta.status_code == 400


def test_rf11_carta_membretada_con_texto_se_emite():
    tipo = DocumentTypeFactory(name="Carta membretada", template_key="carta_membretada")
    inscripcion = EnrollmentFactory()
    client = APIClient()
    client.force_authenticate(user=_direccion())

    respuesta = client.post(
        "/api/v1/documents/issue/",
        {
            "enrollment": str(inscripcion.public_id),
            "document_type": str(tipo.public_id),
            "custom_text": "A quien corresponda: se recomienda ampliamente al estudiante.",
        },
    )

    assert respuesta.status_code == 200
    documento = IssuedDocument.objects.get(enrollment=inscripcion)
    assert "recomienda" in documento.custom_text


def test_rf11_la_constancia_de_solvencia_no_se_emite_por_este_camino():
    """RF-08 tiene su propio endpoint (con la validación de RN-08/RN-09)
    — este atajo no debe poder saltárselo."""
    tipo = DocumentTypeFactory()  # template_key="constancia_solvencia" por default
    inscripcion = EnrollmentFactory()
    client = APIClient()
    client.force_authenticate(user=_direccion())

    respuesta = client.post(
        "/api/v1/documents/issue/",
        {"enrollment": str(inscripcion.public_id), "document_type": str(tipo.public_id)},
    )

    assert respuesta.status_code == 400


def test_rf11_pagos_no_puede_emitir_documentos_generales_acceso_no_autorizado():
    """Nota 1 de docs/permisos-roles.md: el alcance de Pagos sobre
    "Documentos emitidos" es solo para la constancia de solvencia."""
    tipo = DocumentTypeFactory(name="Constancia de estudio", template_key="constancia_estudio")
    inscripcion = EnrollmentFactory()
    rol_pagos = RoleFactory(name="Encargado de pagos", permissions={"documentos": "editar"})
    usuario_pagos = UserFactory(role=rol_pagos)
    client = APIClient()
    client.force_authenticate(user=usuario_pagos)

    respuesta = client.post(
        "/api/v1/documents/issue/",
        {"enrollment": str(inscripcion.public_id), "document_type": str(tipo.public_id)},
    )

    assert respuesta.status_code == 400


def test_rf11_familia_ve_sus_documentos_emitidos_y_puede_volver_a_descargarlos():
    from apps.students.services.link import vincular_encargado_estudiante
    from apps.students.tests.factories import GuardianFactory, StudentFactory

    tipo = DocumentTypeFactory(name="Constancia de estudio", template_key="constancia_estudio")
    rol_familia = RoleFactory(name="Padre de familia", permissions={"documentos": "ver"})
    usuario_familia = UserFactory(role=rol_familia)
    encargado = GuardianFactory(user=usuario_familia)
    mi_hijo = StudentFactory(internal_code="ES020")
    vincular_encargado_estudiante(guardian=encargado, student=mi_hijo, relationship="Padre")
    mi_inscripcion = EnrollmentFactory(student=mi_hijo)

    client_direccion = APIClient()
    client_direccion.force_authenticate(user=_direccion())
    client_direccion.post(
        "/api/v1/documents/issue/",
        {"enrollment": str(mi_inscripcion.public_id), "document_type": str(tipo.public_id)},
    )
    documento = IssuedDocument.objects.get(enrollment=mi_inscripcion)

    client_familia = APIClient()
    client_familia.force_authenticate(user=usuario_familia)

    lista = client_familia.get("/api/v1/documents/")
    assert lista.data["count"] == 1

    descarga = client_familia.get(f"/api/v1/documents/{documento.public_id}/download/")
    assert descarga.status_code == 200
    assert descarga.content[:4] == b"%PDF"
