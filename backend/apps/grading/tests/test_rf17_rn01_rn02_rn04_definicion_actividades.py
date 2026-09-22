import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import Course
from apps.catalog.tests.factories import CourseFactory, GradingUnitFactory, SectionFactory
from apps.grading.models import Activity
from apps.scheduling.models import TeacherAssignment

from .factories import ActivityFactory, ActivityTypeFactory, TeacherAssignmentFactory


def _docente_con_asignacion():
    rol = RoleFactory(name="Docente", permissions={"notas": "editar"})
    docente = UserFactory(role=rol)
    asignacion = TeacherAssignmentFactory(teacher=docente)
    unidad = GradingUnitFactory(cycle=asignacion.cycle)
    return docente, asignacion, unidad


@pytest.mark.django_db
def test_rf17_docente_define_una_actividad_de_su_propia_asignacion():
    docente, asignacion, unidad = _docente_con_asignacion()
    tipo = ActivityTypeFactory(name="Tarea", counts_as_short_quiz=False)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/activities/",
        {
            "assignment": str(asignacion.public_id),
            "unit": str(unidad.public_id),
            "activity_type": str(tipo.public_id),
            "name": "Tarea de fracciones",
            "max_score": "20",
            "due_date": "2026-02-05",
        },
        format="json",
    )

    assert respuesta.status_code == 201


@pytest.mark.django_db
def test_rn02_no_se_puede_pasar_de_cien_puntos_en_la_unidad():
    docente, asignacion, unidad = _docente_con_asignacion()
    tipo = ActivityTypeFactory(name="Proyecto", counts_as_short_quiz=False)
    ActivityFactory(assignment=asignacion, unit=unidad, activity_type=tipo, max_score=70)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/activities/",
        {
            "assignment": str(asignacion.public_id),
            "unit": str(unidad.public_id),
            "activity_type": str(tipo.public_id),
            "name": "Otra actividad",
            "max_score": "40",
            "due_date": "2026-02-06",
        },
        format="json",
    )

    assert respuesta.status_code == 400
    assert Activity.objects.count() == 1


@pytest.mark.django_db
def test_adr0001_no_se_pueden_definir_actividades_para_un_curso_de_taller():
    rol = RoleFactory(name="Tallerista", permissions={"notas": "sin_acceso"})
    tallerista = UserFactory(role=rol)
    seccion = SectionFactory(type="taller")
    curso = CourseFactory(type=Course.TIPO_TALLER)
    asignacion = TeacherAssignment.objects.create(
        teacher=tallerista, course=curso, section=seccion, cycle=seccion.cycle
    )

    client = APIClient()
    client.force_authenticate(user=tallerista)

    respuesta = client.post(
        "/api/v1/activities/",
        {"assignment": str(asignacion.public_id)},
        format="json",
    )

    # Sin acceso al área "notas" en absoluto — ni siquiera llega a la
    # validación de dominio.
    assert respuesta.status_code == 403


@pytest.mark.django_db
def test_docente_no_puede_definir_actividades_de_una_asignacion_ajena_acceso_no_autorizado():
    rol = RoleFactory(name="Docente", permissions={"notas": "editar"})
    docente = UserFactory(role=rol)
    asignacion_ajena = TeacherAssignmentFactory()
    unidad = GradingUnitFactory(cycle=asignacion_ajena.cycle)
    tipo = ActivityTypeFactory()

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/activities/",
        {
            "assignment": str(asignacion_ajena.public_id),
            "unit": str(unidad.public_id),
            "activity_type": str(tipo.public_id),
            "name": "Actividad ajena",
            "max_score": "10",
            "due_date": "2026-02-05",
        },
        format="json",
    )

    assert respuesta.status_code == 403
    assert not Activity.objects.exists()
