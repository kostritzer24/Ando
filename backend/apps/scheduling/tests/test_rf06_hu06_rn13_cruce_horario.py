import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import CourseFactory, SectionFactory
from apps.scheduling.models import ScheduleBlock

from .factories import TeacherAssignmentFactory


def _direccion():
    rol = RoleFactory(name="Dirección", permissions={"horarios_calendario": "editar"})
    return UserFactory(role=rol)


@pytest.mark.django_db
def test_rf06_direccion_arma_un_bloque_de_horario():
    direccion = _direccion()
    asignacion = TeacherAssignmentFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/schedule-blocks/",
        {"assignment": str(asignacion.public_id), "day_of_week": "lunes", "period_number": 1},
        format="json",
    )

    assert respuesta.status_code == 201


@pytest.mark.django_db
def test_rn13_periodo_fuera_de_rango_es_rechazado():
    direccion = _direccion()
    asignacion = TeacherAssignmentFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/schedule-blocks/",
        {"assignment": str(asignacion.public_id), "day_of_week": "lunes", "period_number": 7},
        format="json",
    )

    assert respuesta.status_code == 400
    assert not ScheduleBlock.objects.exists()


@pytest.mark.django_db
def test_hu06_no_se_puede_asignar_al_mismo_docente_en_dos_secciones_en_el_mismo_periodo():
    direccion = _direccion()
    docente = UserFactory(role=RoleFactory(name="Docente"))
    curso_a = CourseFactory()
    curso_b = CourseFactory()
    seccion_a = SectionFactory(grade="Segundo básico")
    seccion_b = SectionFactory(grade="Tercero básico", cycle=seccion_a.cycle)
    asignacion_a = TeacherAssignmentFactory(
        teacher=docente, course=curso_a, section=seccion_a, cycle=seccion_a.cycle
    )
    asignacion_b = TeacherAssignmentFactory(
        teacher=docente, course=curso_b, section=seccion_b, cycle=seccion_a.cycle
    )

    client = APIClient()
    client.force_authenticate(user=direccion)

    primera = client.post(
        "/api/v1/schedule-blocks/",
        {"assignment": str(asignacion_a.public_id), "day_of_week": "lunes", "period_number": 1},
        format="json",
    )
    segunda = client.post(
        "/api/v1/schedule-blocks/",
        {"assignment": str(asignacion_b.public_id), "day_of_week": "lunes", "period_number": 1},
        format="json",
    )

    assert primera.status_code == 201
    assert segunda.status_code == 400
    assert ScheduleBlock.objects.count() == 1


@pytest.mark.django_db
def test_el_mismo_docente_puede_tener_clases_en_periodos_distintos_el_mismo_dia():
    direccion = _direccion()
    docente = UserFactory(role=RoleFactory(name="Docente"))
    curso_a = CourseFactory()
    curso_b = CourseFactory()
    seccion_a = SectionFactory(grade="Segundo básico")
    seccion_b = SectionFactory(grade="Tercero básico", cycle=seccion_a.cycle)
    asignacion_a = TeacherAssignmentFactory(
        teacher=docente, course=curso_a, section=seccion_a, cycle=seccion_a.cycle
    )
    asignacion_b = TeacherAssignmentFactory(
        teacher=docente, course=curso_b, section=seccion_b, cycle=seccion_a.cycle
    )

    client = APIClient()
    client.force_authenticate(user=direccion)

    primera = client.post(
        "/api/v1/schedule-blocks/",
        {"assignment": str(asignacion_a.public_id), "day_of_week": "lunes", "period_number": 1},
        format="json",
    )
    segunda = client.post(
        "/api/v1/schedule-blocks/",
        {"assignment": str(asignacion_b.public_id), "day_of_week": "lunes", "period_number": 2},
        format="json",
    )

    assert primera.status_code == 201
    assert segunda.status_code == 201


@pytest.mark.django_db
def test_docente_no_puede_armar_el_horario_acceso_no_autorizado():
    rol_docente = RoleFactory(name="Docente", permissions={"horarios_calendario": "editar"})
    docente = UserFactory(role=rol_docente)
    asignacion = TeacherAssignmentFactory(teacher=docente)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/schedule-blocks/",
        {"assignment": str(asignacion.public_id), "day_of_week": "lunes", "period_number": 1},
        format="json",
    )

    assert respuesta.status_code == 403
    assert not ScheduleBlock.objects.exists()


@pytest.mark.django_db
def test_docente_solo_ve_sus_propios_bloques_de_horario():
    rol_docente = RoleFactory(name="Docente", permissions={"horarios_calendario": "ver"})
    docente = UserFactory(role=rol_docente)
    asignacion_propia = TeacherAssignmentFactory(teacher=docente)
    asignacion_ajena = TeacherAssignmentFactory()

    ScheduleBlock.objects.create(assignment=asignacion_propia, day_of_week="lunes", period_number=1)
    ScheduleBlock.objects.create(assignment=asignacion_ajena, day_of_week="lunes", period_number=1)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/schedule-blocks/")

    assert respuesta.data["count"] == 1


@pytest.mark.django_db
def test_rn13_una_seccion_no_tiene_dos_cursos_a_la_misma_hora():
    """Hallazgo B-021: el horario permitía dos clases simultáneas en una sección."""
    client = APIClient()
    client.force_authenticate(user=_direccion())
    primera = TeacherAssignmentFactory()
    segunda = TeacherAssignmentFactory(section=primera.section, cycle=primera.cycle)
    datos = {"day_of_week": "lunes", "period_number": 1}
    assert (
        client.post(
            "/api/v1/schedule-blocks/",
            {"assignment": str(primera.public_id), **datos},
            format="json",
        ).status_code
        == 201
    )

    respuesta = client.post(
        "/api/v1/schedule-blocks/", {"assignment": str(segunda.public_id), **datos}, format="json"
    )

    assert respuesta.status_code == 400
    assert ScheduleBlock.objects.count() == 1
