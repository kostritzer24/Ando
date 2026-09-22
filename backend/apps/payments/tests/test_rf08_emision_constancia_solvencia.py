import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import DocumentTypeFactory, ScholarshipFactory
from apps.documents.models import IssuedDocument
from apps.students.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


def _usuario_pagos():
    rol = RoleFactory(name="Encargado de pagos", permissions={"pagos_solvencia": "editar"})
    return UserFactory(role=rol)


def test_rf08_no_se_puede_emitir_constancia_de_un_estudiante_insolvente():
    DocumentTypeFactory()
    inscripcion = EnrollmentFactory()  # sin pagos, sin beca: insolvente.
    client = APIClient()
    client.force_authenticate(user=_usuario_pagos())

    respuesta = client.post(f"/api/v1/solvency/{inscripcion.public_id}/certificate/")

    assert respuesta.status_code == 400
    assert IssuedDocument.objects.count() == 0


def test_rf08_emite_la_constancia_en_pdf_para_un_estudiante_solvente():
    DocumentTypeFactory()
    beca = ScholarshipFactory()
    inscripcion = EnrollmentFactory(scholarship=beca)
    client = APIClient()
    client.force_authenticate(user=_usuario_pagos())

    respuesta = client.post(f"/api/v1/solvency/{inscripcion.public_id}/certificate/")

    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta.content[:4] == b"%PDF"

    documento = IssuedDocument.objects.get(enrollment=inscripcion)
    assert documento.document_type.template_key == "constancia_solvencia"
    assert documento.issued_by.role.name == "Encargado de pagos"
    assert len(documento.verification_code) == 12


def test_rf08_familia_no_puede_emitir_la_constancia_acceso_no_autorizado():
    DocumentTypeFactory()
    beca = ScholarshipFactory()
    inscripcion = EnrollmentFactory(scholarship=beca)
    rol_familia = RoleFactory(name="Padre de familia", permissions={"pagos_solvencia": "ver"})
    familia = UserFactory(role=rol_familia)
    client = APIClient()
    client.force_authenticate(user=familia)

    respuesta = client.post(f"/api/v1/solvency/{inscripcion.public_id}/certificate/")

    assert respuesta.status_code == 403
