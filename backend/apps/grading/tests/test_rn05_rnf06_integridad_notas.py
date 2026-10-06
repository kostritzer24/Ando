"""RN-05, RN-01/RN-02 y RNF-06 sobre la API: lo que el modelo de notas
promete (el punteo real no se altera, la unidad no pasa de 100 puntos,
todo cambio queda en bitácora) se cumple también contra llamadas directas
a la API, no solo por el camino que ofrece la interfaz."""

from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.core.models import AuditLog
from apps.grading.models import Activity, Grade, GradeChangeRequest
from apps.grading.services.grade import nota_de_unidad
from apps.students.tests.factories import EnrollmentFactory

from .factories import ActivityFactory, TeacherAssignmentFactory


def _escenario():
    docente = UserFactory(role=RoleFactory(name="Docente", permissions={"notas": "editar"}))
    asignacion = TeacherAssignmentFactory(teacher=docente)
    a1 = ActivityFactory(assignment=asignacion, max_score=50, name="A1")
    a2 = ActivityFactory(assignment=asignacion, unit=a1.unit, max_score=50, name="A2")
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    client = APIClient()
    client.force_authenticate(user=docente)
    return docente, asignacion, a1, a2, inscripcion, client


def _nota(docente, inscripcion, actividad, punteo=30):
    return Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad,
        raw_score=punteo,
        current_score=punteo,
        recorded_by=docente,
    )


def _direccion():
    return UserFactory(
        role=RoleFactory(
            name="Dirección", permissions={"notas": "editar", "modificacion_notas": "editar"}
        )
    )


# --- Notas: solo se crean y se consultan --------------------------------


@pytest.mark.django_db
def test_rn05_una_nota_no_se_puede_borrar_por_la_api():
    docente, _, a1, _, inscripcion, client = _escenario()
    nota = _nota(docente, inscripcion, a1)

    respuesta = client.delete(f"/api/v1/grades/{nota.public_id}/")

    assert respuesta.status_code == 405
    assert Grade.objects.filter(pk=nota.pk).exists()


@pytest.mark.django_db
def test_rn05_una_nota_no_se_puede_editar_ni_mover_a_otra_actividad():
    docente, _, a1, a2, inscripcion, client = _escenario()
    nota = _nota(docente, inscripcion, a1)

    respuesta = client.patch(
        f"/api/v1/grades/{nota.public_id}/", {"activity": str(a2.public_id)}, format="json"
    )

    assert respuesta.status_code == 405
    nota.refresh_from_db()
    assert nota.activity == a1


@pytest.mark.django_db
def test_rf18_no_se_califica_a_un_estudiante_de_otra_seccion():
    _, _, a1, _, _, client = _escenario()
    de_otra_seccion = EnrollmentFactory()

    respuesta = client.post(
        "/api/v1/grades/",
        {
            "enrollment": str(de_otra_seccion.public_id),
            "activity": str(a1.public_id),
            "raw_score": "8",
        },
        format="json",
    )

    assert respuesta.status_code == 400
    assert "enrollment" in respuesta.data
    assert not Grade.objects.exists()


@pytest.mark.django_db
def test_rnf06_registrar_una_nota_deja_bitacora():
    docente, _, a1, _, inscripcion, client = _escenario()

    client.post(
        "/api/v1/grades/",
        {
            "enrollment": str(inscripcion.public_id),
            "activity": str(a1.public_id),
            "raw_score": "42",
        },
        format="json",
    )

    registro = AuditLog.objects.get(entity_name="grading.Grade")
    assert registro.user == docente
    assert registro.action == "crear"
    assert registro.new_value["raw_score"] == "42.00"


@pytest.mark.django_db
def test_listar_notas_no_hace_una_consulta_por_fila():
    docente, _, a1, a2, _, client = _escenario()
    for _ in range(15):
        inscripcion = EnrollmentFactory(section=a1.assignment.section, cycle=a1.assignment.cycle)
        _nota(docente, inscripcion, a1)
        _nota(docente, inscripcion, a2)

    with CaptureQueriesContext(connection) as consultas:
        respuesta = client.get("/api/v1/grades/?page_size=200")

    assert len(respuesta.data["results"]) == 30
    assert len(consultas) < 15  # antes: ~6 por fila (183 para estas 30)


# --- Actividades: el tope de 100 se respeta también al editar ----------


@pytest.mark.django_db
def test_rn02_editar_el_maximo_no_puede_pasar_los_cien_puntos():
    _, _, a1, _, _, client = _escenario()

    respuesta = client.patch(
        f"/api/v1/activities/{a1.public_id}/", {"max_score": "90"}, format="json"
    )

    assert respuesta.status_code == 400
    a1.refresh_from_db()
    assert a1.max_score == 50


@pytest.mark.django_db
def test_rf17_editar_una_actividad_sin_notas_queda_en_bitacora():
    _, _, a1, a2, _, client = _escenario()
    client.delete(f"/api/v1/activities/{a2.public_id}/")

    respuesta = client.patch(
        f"/api/v1/activities/{a1.public_id}/", {"max_score": "100", "name": "Examen"}, format="json"
    )

    assert respuesta.status_code == 200
    assert respuesta.data["max_score"] == "100.00"
    registro = AuditLog.objects.filter(entity_name="grading.Activity", action="actualizar").get()
    assert registro.old_value["max_score"] == "50.00"
    assert registro.new_value["name"] == "Examen"


@pytest.mark.django_db
def test_rn05_una_actividad_calificada_no_cambia_su_maximo():
    docente, _, a1, a2, inscripcion, client = _escenario()
    client.delete(f"/api/v1/activities/{a2.public_id}/")
    _nota(docente, inscripcion, a1, punteo=45)

    respuesta = client.patch(
        f"/api/v1/activities/{a1.public_id}/", {"max_score": "40"}, format="json"
    )

    assert respuesta.status_code == 400
    assert "ya tiene notas" in str(respuesta.data)


@pytest.mark.django_db
def test_rf17_editar_no_mueve_la_actividad_a_otra_asignacion():
    _, _, a1, _, _, client = _escenario()
    otra = TeacherAssignmentFactory()

    client.patch(
        f"/api/v1/activities/{a1.public_id}/", {"assignment": str(otra.public_id)}, format="json"
    )

    a1.refresh_from_db()
    assert a1.assignment != otra


@pytest.mark.django_db
def test_baja_de_actividad_sin_notas_es_logica_y_libera_sus_puntos():
    _, _, a1, a2, _, client = _escenario()

    respuesta = client.delete(f"/api/v1/activities/{a2.public_id}/")

    assert respuesta.status_code == 204
    a2.refresh_from_db()
    assert a2.is_active is False
    assert AuditLog.objects.filter(entity_name="grading.Activity", action="eliminar").exists()


@pytest.mark.django_db
def test_rn01_una_actividad_calificada_no_se_da_de_baja():
    docente, _, a1, a2, inscripcion, client = _escenario()
    _nota(docente, inscripcion, a2, punteo=50)

    respuesta = client.delete(f"/api/v1/activities/{a2.public_id}/")

    assert respuesta.status_code == 400
    assert Activity.objects.get(pk=a2.pk).is_active is True


@pytest.mark.django_db
def test_rn01_is_active_no_se_cambia_por_patch():
    _, _, a1, _, _, client = _escenario()

    client.patch(f"/api/v1/activities/{a1.public_id}/", {"is_active": False}, format="json")

    a1.refresh_from_db()
    assert a1.is_active is True


@pytest.mark.django_db
def test_rn01_la_nota_de_unidad_no_cuenta_actividades_dadas_de_baja():
    docente, asignacion, a1, a2, inscripcion, _ = _escenario()
    _nota(docente, inscripcion, a1, punteo=40)
    _nota(docente, inscripcion, a2, punteo=50)
    Activity.objects.filter(pk=a2.pk).update(is_active=False)

    nota = nota_de_unidad(enrollment=inscripcion, unit=a1.unit, assignment=asignacion)

    assert nota == Decimal("40")


# --- Solicitudes de modificación ---------------------------------------


def _solicitar(client, nota, punteo):
    return client.post(
        "/api/v1/grade-change-requests/",
        {"grade": str(nota.public_id), "requested_score": punteo, "reason": "Corrección."},
        format="json",
    )


@pytest.mark.django_db
def test_rn05_una_solicitud_ya_rechazada_no_se_puede_aprobar_despues():
    docente, _, a1, _, inscripcion, client = _escenario()
    nota = _nota(docente, inscripcion, a1)
    solicitud = _solicitar(client, nota, "45").data
    client.force_authenticate(user=_direccion())
    client.post(
        f"/api/v1/grade-change-requests/{solicitud['public_id']}/reject/",
        {"motivo": "No corresponde."},
        format="json",
    )

    respuesta = client.post(f"/api/v1/grade-change-requests/{solicitud['public_id']}/approve/")

    assert respuesta.status_code == 400
    nota.refresh_from_db()
    assert nota.current_score == 30


@pytest.mark.django_db
def test_rf23_no_se_abre_una_segunda_solicitud_mientras_hay_una_pendiente():
    docente, _, a1, _, inscripcion, client = _escenario()
    nota = _nota(docente, inscripcion, a1)
    _solicitar(client, nota, "45")

    respuesta = _solicitar(client, nota, "20")

    assert respuesta.status_code == 400
    assert GradeChangeRequest.objects.count() == 1


@pytest.mark.django_db
def test_rf23_la_nota_original_de_una_solicitud_es_la_vigente():
    docente, _, a1, _, inscripcion, client = _escenario()
    nota = _nota(docente, inscripcion, a1, punteo=30)
    primera = _solicitar(client, nota, "45").data
    direccion = APIClient()
    direccion.force_authenticate(user=_direccion())
    direccion.post(f"/api/v1/grade-change-requests/{primera['public_id']}/approve/")

    segunda = _solicitar(client, nota, "40")

    assert segunda.status_code == 201
    assert segunda.data["original_score"] == "45.00"  # no el punteo real (30)


@pytest.mark.django_db
def test_rf23_proponer_la_misma_nota_vigente_es_rechazado():
    docente, _, a1, _, inscripcion, client = _escenario()
    nota = _nota(docente, inscripcion, a1, punteo=30)

    respuesta = _solicitar(client, nota, "30")

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_rf23_punteo_propuesto_fuera_de_rango_responde_400():
    docente, _, a1, _, inscripcion, client = _escenario()
    nota = _nota(docente, inscripcion, a1)

    respuesta = _solicitar(client, nota, "51")

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_rnf06_aprobar_una_modificacion_deja_la_nota_anterior_y_la_nueva_en_bitacora():
    docente, _, a1, _, inscripcion, client = _escenario()
    nota = _nota(docente, inscripcion, a1, punteo=30)
    solicitud = _solicitar(client, nota, "45").data
    direccion = _direccion()
    client.force_authenticate(user=direccion)

    client.post(f"/api/v1/grade-change-requests/{solicitud['public_id']}/approve/")

    cambio = AuditLog.objects.get(entity_name="grading.Grade", action="actualizar")
    assert cambio.user == direccion
    assert cambio.old_value == {"current_score": "30.00"}
    assert cambio.new_value == {"current_score": "45.00"}
    assert AuditLog.objects.filter(
        entity_name="grading.GradeChangeRequest", new_value__status="aprobada"
    ).exists()
