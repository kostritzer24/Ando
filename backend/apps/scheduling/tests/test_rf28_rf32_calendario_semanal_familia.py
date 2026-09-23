import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.scheduling.models import CalendarEvent, ScheduleBlock
from apps.students.services.link import vincular_encargado_estudiante
from apps.students.tests.factories import EnrollmentFactory, GuardianFactory, StudentFactory

from .factories import TeacherAssignmentFactory

pytestmark = pytest.mark.django_db


def _familia_con_hijo():
    rol = RoleFactory(name="Padre de familia", permissions={"horarios_calendario": "ver"})
    usuario = UserFactory(role=rol)
    encargado = GuardianFactory(user=usuario)
    hijo = StudentFactory()
    vincular_encargado_estudiante(guardian=encargado, student=hijo, relationship="Madre")
    return usuario, hijo


def test_rf28_rf32_familia_ve_el_horario_y_los_eventos_de_la_seccion_del_hijo():
    usuario, hijo = _familia_con_hijo()
    asignacion = TeacherAssignmentFactory()
    inscripcion = EnrollmentFactory(student=hijo, section=asignacion.section, cycle=asignacion.cycle)
    ScheduleBlock.objects.create(assignment=asignacion, day_of_week="lunes", period_number=1)
    CalendarEvent.objects.create(
        title="Aviso institucional",
        type=CalendarEvent.TIPO_INSTITUCIONAL,
        event_date="2026-03-10",
        start_time="08:00",
        end_time="08:30",
        published_by=asignacion.teacher,
    )
    CalendarEvent.objects.create(
        title="Entrega de proyecto",
        type=CalendarEvent.TIPO_ASIGNACION_DOCENTE,
        event_date="2026-03-11",
        start_time="09:00",
        end_time="10:00",
        assignment=asignacion,
        published_by=asignacion.teacher,
    )

    client = APIClient()
    client.force_authenticate(user=usuario)
    respuesta = client.get(f"/api/v1/calendar/weekly/?student={hijo.public_id}")

    assert respuesta.status_code == 200
    assert len(respuesta.data["schedule"]) == 1
    assert respuesta.data["schedule"][0]["day_of_week"] == "lunes"
    titulos = {e["title"] for e in respuesta.data["events"]}
    assert titulos == {"Aviso institucional", "Entrega de proyecto"}
    assert inscripcion.student_id == hijo.id  # la inscripción sí es del hijo elegido.


def test_rf28_rf32_no_incluye_eventos_de_otra_seccion():
    usuario, hijo = _familia_con_hijo()
    asignacion = TeacherAssignmentFactory()
    EnrollmentFactory(student=hijo, section=asignacion.section, cycle=asignacion.cycle)
    otra_asignacion = TeacherAssignmentFactory()
    ScheduleBlock.objects.create(assignment=otra_asignacion, day_of_week="martes", period_number=2)
    CalendarEvent.objects.create(
        title="Evento de otra sección",
        type=CalendarEvent.TIPO_ASIGNACION_DOCENTE,
        event_date="2026-03-12",
        start_time="09:00",
        end_time="10:00",
        assignment=otra_asignacion,
        published_by=otra_asignacion.teacher,
    )

    client = APIClient()
    client.force_authenticate(user=usuario)
    respuesta = client.get(f"/api/v1/calendar/weekly/?student={hijo.public_id}")

    assert respuesta.data["schedule"] == []
    assert respuesta.data["events"] == []


def test_rf28_rf32_no_se_puede_consultar_un_estudiante_ajeno():
    usuario, _hijo = _familia_con_hijo()
    otro_estudiante = StudentFactory()

    client = APIClient()
    client.force_authenticate(user=usuario)
    respuesta = client.get(f"/api/v1/calendar/weekly/?student={otro_estudiante.public_id}")

    assert respuesta.status_code == 404


def test_rf28_rf32_solo_es_para_el_portal_de_familias():
    rol = RoleFactory(name="Docente", permissions={"horarios_calendario": "editar"})
    docente = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=docente)
    respuesta = client.get("/api/v1/calendar/weekly/?student=00000000-0000-0000-0000-000000000000")

    assert respuesta.status_code == 403
