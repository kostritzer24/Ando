import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import DocumentTypeFactory, SectionFactory
from apps.grading.models import Grade
from apps.grading.services.consolidado import consolidado_de_notas
from apps.grading.tests.factories import ActivityFactory, TeacherAssignmentFactory
from apps.students.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


def _direccion():
    rol = RoleFactory(name="Dirección", permissions={"documentos": "editar"})
    return UserFactory(role=rol)


def _emitir(inscripcion):
    tipo = DocumentTypeFactory(name="Cierre de pensum", template_key="cierre_pensum")
    client = APIClient()
    client.force_authenticate(user=_direccion())
    return client.post(
        "/api/v1/documents/issue/",
        {"enrollment": str(inscripcion.public_id), "document_type": str(tipo.public_id)},
    )


def test_rf11_cierre_de_pensum_se_emite_para_quinto_bachillerato():
    seccion = SectionFactory(grade="Quinto bachillerato")
    inscripcion = EnrollmentFactory(section=seccion, cycle=seccion.cycle)

    respuesta = _emitir(inscripcion)

    assert respuesta.status_code == 200
    assert respuesta.content[:4] == b"%PDF"


def test_rf11_cierre_de_pensum_se_rechaza_fuera_de_quinto_bachillerato():
    seccion = SectionFactory(grade="Cuarto bachillerato")
    inscripcion = EnrollmentFactory(section=seccion, cycle=seccion.cycle)

    respuesta = _emitir(inscripcion)

    assert respuesta.status_code == 400


def test_rf11_el_consolidado_trae_nota_final_por_curso_y_promedio_por_anio():
    asignacion = TeacherAssignmentFactory(section__grade="Quinto bachillerato")
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    actividad = ActivityFactory(assignment=asignacion, max_score=100)
    Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad,
        raw_score=80,
        current_score=80,
        recorded_by=UserFactory(),
    )

    consolidado = consolidado_de_notas(inscripcion.student)

    assert len(consolidado["anios"]) == 1
    anio = consolidado["anios"][0]
    assert anio["cursos"][0]["promedio"] == 80
    assert anio["promedio_anual"] == 80
    assert consolidado["promedio_general"] == 80
