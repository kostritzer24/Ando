import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.scheduling.models import CalendarEvent

from .factories import TeacherAssignmentFactory


def _docente():
    rol = RoleFactory(name="Docente", permissions={"horarios_calendario": "editar"})
    return UserFactory(role=rol)


def _direccion():
    rol = RoleFactory(name="Dirección", permissions={"horarios_calendario": "editar"})
    return UserFactory(role=rol)


@pytest.mark.django_db
def test_rf22_docente_publica_un_evento_de_su_propia_asignacion():
    docente = _docente()
    asignacion = TeacherAssignmentFactory(teacher=docente)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/calendar-events/",
        {
            "title": "Entrega de tarea de fracciones",
            "type": "asignacion_docente",
            "event_date": "2099-02-10",
            "start_time": "08:00:00",
            "end_time": "08:40:00",
            "assignment": str(asignacion.public_id),
        },
        format="json",
    )

    assert respuesta.status_code == 201


@pytest.mark.django_db
def test_rn17_docente_no_puede_publicar_un_evento_institucional():
    docente = _docente()

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/calendar-events/",
        {
            "title": "Día del cariño",
            "type": "institucional",
            "event_date": "2099-02-14",
            "start_time": "08:00:00",
            "end_time": "12:40:00",
        },
        format="json",
    )

    assert respuesta.status_code == 400
    assert not CalendarEvent.objects.exists()


@pytest.mark.django_db
def test_docente_no_puede_publicar_la_asignacion_de_otro_docente():
    docente = _docente()
    asignacion_ajena = TeacherAssignmentFactory()

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/calendar-events/",
        {
            "title": "Examen",
            "type": "asignacion_docente",
            "event_date": "2099-02-10",
            "start_time": "08:00:00",
            "end_time": "08:40:00",
            "assignment": str(asignacion_ajena.public_id),
        },
        format="json",
    )

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_rn17_el_evento_de_otro_docente_ni_siquiera_aparece_acceso_no_autorizado():
    """El alcance se filtra en el queryset (sección 14.2): un evento de
    tipo 'asignacion_docente' publicado por otro docente no entra en el
    scope, así que cambiar el UUID en la URL da 404, no 403 — nunca
    revela que el recurso existe."""
    docente = _docente()
    otro_docente = _docente()
    evento_ajeno = CalendarEvent.objects.create(
        title="Evento ajeno",
        type=CalendarEvent.TIPO_ASIGNACION_DOCENTE,
        event_date="2026-02-10",
        start_time="08:00:00",
        end_time="08:40:00",
        assignment=TeacherAssignmentFactory(teacher=otro_docente),
        published_by=otro_docente,
    )

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.patch(
        f"/api/v1/calendar-events/{evento_ajeno.public_id}/",
        {"title": "Lo cambio igual"},
        format="json",
    )

    assert respuesta.status_code == 404
    evento_ajeno.refresh_from_db()
    assert evento_ajeno.title == "Evento ajeno"


@pytest.mark.django_db
def test_rn17_docente_ve_un_evento_institucional_pero_no_puede_editarlo_acceso_no_autorizado():
    """Un evento institucional sí está dentro del scope de lectura de
    cualquier docente (lo necesita para ver el calendario completo), pero
    eso no le da permiso de escritura — acá sí corresponde 403, porque el
    objeto existe dentro de su alcance de lectura."""
    docente = _docente()
    direccion = _direccion()
    institucional = CalendarEvent.objects.create(
        title="Día del cariño",
        type=CalendarEvent.TIPO_INSTITUCIONAL,
        event_date="2026-02-14",
        start_time="08:00:00",
        end_time="12:40:00",
        published_by=direccion,
    )

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.patch(
        f"/api/v1/calendar-events/{institucional.public_id}/",
        {"title": "Lo cambio igual"},
        format="json",
    )

    assert respuesta.status_code == 403
    institucional.refresh_from_db()
    assert institucional.title == "Día del cariño"


@pytest.mark.django_db
def test_rn17_direccion_puede_editar_cualquier_evento():
    docente = _docente()
    direccion = _direccion()
    evento = CalendarEvent.objects.create(
        title="Evento del docente",
        type=CalendarEvent.TIPO_ASIGNACION_DOCENTE,
        event_date="2026-02-10",
        start_time="08:00:00",
        end_time="08:40:00",
        assignment=TeacherAssignmentFactory(teacher=docente),
        published_by=docente,
    )

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.patch(
        f"/api/v1/calendar-events/{evento.public_id}/",
        {"title": "Corregido por Dirección"},
        format="json",
    )

    assert respuesta.status_code == 200
    evento.refresh_from_db()
    assert evento.title == "Corregido por Dirección"


@pytest.mark.django_db
def test_docente_ve_sus_propios_eventos_y_los_institucionales_no_los_de_otros():
    docente = _docente()
    otro_docente = _docente()
    direccion = _direccion()

    mio = CalendarEvent.objects.create(
        title="Mío",
        type=CalendarEvent.TIPO_ASIGNACION_DOCENTE,
        event_date="2026-02-10",
        start_time="08:00:00",
        end_time="08:40:00",
        assignment=TeacherAssignmentFactory(teacher=docente),
        published_by=docente,
    )
    institucional = CalendarEvent.objects.create(
        title="Institucional",
        type=CalendarEvent.TIPO_INSTITUCIONAL,
        event_date="2026-02-14",
        start_time="08:00:00",
        end_time="12:40:00",
        published_by=direccion,
    )
    CalendarEvent.objects.create(
        title="Ajeno",
        type=CalendarEvent.TIPO_ASIGNACION_DOCENTE,
        event_date="2026-02-10",
        start_time="08:00:00",
        end_time="08:40:00",
        assignment=TeacherAssignmentFactory(teacher=otro_docente),
        published_by=otro_docente,
    )

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/calendar-events/")
    titulos = {evento["title"] for evento in respuesta.data["results"]}

    assert titulos == {mio.title, institucional.title}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "cambios,campo",
    [
        ({"start_time": "10:00:00", "end_time": "09:00:00"}, "end_time"),  # fin antes del inicio
        ({"event_date": "2020-01-10"}, "event_date"),  # fecha que ya pasó
    ],
)
def test_rf22_un_evento_con_horas_o_fecha_imposibles_responde_400(cambios, campo):
    """Hallazgos B-003 y D-012."""
    rol = RoleFactory(name="Dirección", permissions={"horarios_calendario": "editar"})
    client = APIClient()
    client.force_authenticate(user=UserFactory(role=rol))
    datos = {
        "title": "Reunión",
        "type": "institucional",
        "event_date": "2099-02-10",
        "start_time": "08:00:00",
        "end_time": "09:00:00",
        **cambios,
    }

    respuesta = client.post("/api/v1/calendar-events/", datos, format="json")

    assert respuesta.status_code == 400
    assert campo in respuesta.data
