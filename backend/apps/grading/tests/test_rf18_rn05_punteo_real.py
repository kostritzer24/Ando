import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.grading.models import Grade
from apps.students.tests.factories import EnrollmentFactory

from .factories import ActivityFactory, TeacherAssignmentFactory


def _docente_con_actividad(max_score=10):
    rol = RoleFactory(name="Docente", permissions={"notas": "editar"})
    docente = UserFactory(role=rol)
    asignacion = TeacherAssignmentFactory(teacher=docente)
    actividad = ActivityFactory(assignment=asignacion, max_score=max_score)
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    return docente, actividad, inscripcion


@pytest.mark.django_db
def test_rf18_docente_registra_el_punteo_real():
    docente, actividad, inscripcion = _docente_con_actividad()

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grades/",
        {
            "enrollment": str(inscripcion.public_id),
            "activity": str(actividad.public_id),
            "raw_score": "8.5",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["current_score"] == "8.50"


@pytest.mark.django_db
def test_rn01_punteo_fuera_del_maximo_de_la_actividad_es_rechazado():
    docente, actividad, inscripcion = _docente_con_actividad(max_score=10)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grades/",
        {
            "enrollment": str(inscripcion.public_id),
            "activity": str(actividad.public_id),
            "raw_score": "15",
        },
        format="json",
    )

    assert respuesta.status_code == 400
    assert not Grade.objects.exists()


@pytest.mark.django_db
def test_rn05_no_se_puede_calificar_dos_veces_la_misma_actividad():
    docente, actividad, inscripcion = _docente_con_actividad()

    client = APIClient()
    client.force_authenticate(user=docente)

    datos = {
        "enrollment": str(inscripcion.public_id),
        "activity": str(actividad.public_id),
        "raw_score": "8",
    }
    primera = client.post("/api/v1/grades/", datos, format="json")
    segunda = client.post("/api/v1/grades/", {**datos, "raw_score": "9"}, format="json")

    assert primera.status_code == 201
    assert segunda.status_code == 400
    assert Grade.objects.count() == 1
    assert Grade.objects.get().current_score == 8


@pytest.mark.django_db
def test_rn06_la_api_nunca_expone_el_punteo_real_raw_score():
    docente, actividad, inscripcion = _docente_con_actividad()

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grades/",
        {
            "enrollment": str(inscripcion.public_id),
            "activity": str(actividad.public_id),
            "raw_score": "8",
        },
        format="json",
    )

    assert "raw_score" not in respuesta.data

    listado = client.get("/api/v1/grades/")
    assert "raw_score" not in listado.data["results"][0]


@pytest.mark.django_db
def test_docente_no_puede_calificar_una_asignacion_ajena_acceso_no_autorizado():
    rol = RoleFactory(name="Docente", permissions={"notas": "editar"})
    docente = UserFactory(role=rol)
    _otro_docente, actividad_ajena, inscripcion = _docente_con_actividad()

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grades/",
        {
            "enrollment": str(inscripcion.public_id),
            "activity": str(actividad_ajena.public_id),
            "raw_score": "8",
        },
        format="json",
    )

    assert respuesta.status_code == 403
    assert not Grade.objects.exists()
