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
        {"assignment": str(asignacion.public_id), "day_of_week": "lunes", "period_number": 10},
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


def _bloque(client, asignacion, dia="lunes", periodo=1):
    return client.post(
        "/api/v1/schedule-blocks/",
        {"assignment": str(asignacion.public_id), "day_of_week": dia, "period_number": periodo},
        format="json",
    )


@pytest.mark.django_db
def test_hu06_dos_docentes_distintos_no_pueden_dar_clase_a_la_misma_seccion_a_la_misma_hora():
    client = APIClient()
    client.force_authenticate(user=_direccion())
    seccion = SectionFactory()
    docente_1 = TeacherAssignmentFactory(section=seccion, cycle=seccion.cycle)
    docente_2 = TeacherAssignmentFactory(section=seccion, cycle=seccion.cycle)

    assert _bloque(client, docente_1).status_code == 201
    segundo = _bloque(client, docente_2)

    assert segundo.status_code == 400
    assert "ya tiene otro curso" in str(segundo.data)


@pytest.mark.django_db
def test_hu06_repetir_exactamente_el_mismo_bloque_es_un_cruce_no_un_duplicado():
    client = APIClient()
    client.force_authenticate(user=_direccion())
    asignacion = TeacherAssignmentFactory()

    assert _bloque(client, asignacion).status_code == 201
    repetido = _bloque(client, asignacion)

    assert repetido.status_code == 400
    assert ScheduleBlock.objects.count() == 1


@pytest.mark.django_db
def test_hu06_dar_de_baja_una_asignacion_libera_sus_celdas_y_se_puede_reasignar():
    client = APIClient()
    client.force_authenticate(user=_direccion())
    seccion = SectionFactory()
    docente = UserFactory(role=RoleFactory(name="Docente"))
    asignacion = TeacherAssignmentFactory(teacher=docente, section=seccion, cycle=seccion.cycle)
    assert _bloque(client, asignacion).status_code == 201

    baja = client.delete(f"/api/v1/assignments/{asignacion.public_id}/")
    assert baja.status_code == 204

    # La celda queda libre para cualquiera...
    otra = TeacherAssignmentFactory(section=seccion, cycle=seccion.cycle)
    assert _bloque(client, otra).status_code == 201

    # ...y volver a asignar lo mismo reactiva la asignación, no choca.
    datos = {
        "teacher": str(asignacion.teacher.public_id),
        "course": str(asignacion.course.public_id),
        "section": str(seccion.public_id),
        "cycle": str(seccion.cycle.public_id),
    }
    nueva = client.post("/api/v1/assignments/", datos, format="json")
    assert nueva.status_code == 201
    repetida = client.post("/api/v1/assignments/", datos, format="json")
    assert repetida.status_code == 400
    assert "ya tiene asignado" in str(repetida.data)


@pytest.mark.django_db
def test_hu06_mover_un_bloque_a_una_celda_ocupada_tambien_se_rechaza():
    client = APIClient()
    client.force_authenticate(user=_direccion())
    seccion = SectionFactory()
    a = TeacherAssignmentFactory(section=seccion, cycle=seccion.cycle)
    b = TeacherAssignmentFactory(section=seccion, cycle=seccion.cycle)
    _bloque(client, a, periodo=1)
    bloque_b = _bloque(client, b, periodo=2)

    movido = client.patch(
        f"/api/v1/schedule-blocks/{bloque_b.data['public_id']}/",
        {"period_number": 1},
        format="json",
    )

    assert movido.status_code == 400


@pytest.mark.django_db
def test_rn13_los_talleres_usan_la_franja_de_la_tarde_y_los_cursos_la_de_la_mañana():
    client = APIClient()
    client.force_authenticate(user=_direccion())
    curso = TeacherAssignmentFactory()
    taller = TeacherAssignmentFactory(
        course=CourseFactory(type="taller"), section=SectionFactory(type="taller")
    )

    assert _bloque(client, taller, periodo=7).status_code == 201
    assert _bloque(client, taller, dia="martes", periodo=1).status_code == 400
    assert _bloque(client, curso, periodo=8).status_code == 400
