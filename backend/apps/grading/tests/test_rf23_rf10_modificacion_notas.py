import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.grading.models import Grade, GradeChangeRequest
from apps.students.tests.factories import EnrollmentFactory

from .factories import ActivityFactory, TeacherAssignmentFactory


def _docente_con_nota():
    rol = RoleFactory(name="Docente", permissions={"notas": "editar"})
    docente = UserFactory(role=rol)
    asignacion = TeacherAssignmentFactory(teacher=docente)
    actividad = ActivityFactory(assignment=asignacion, max_score=10)
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    calificacion = Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad,
        raw_score=6,
        current_score=6,
        recorded_by=docente,
    )
    return docente, calificacion


@pytest.mark.django_db
def test_rf23_docente_solicita_una_correccion():
    docente, calificacion = _docente_con_nota()

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grade-change-requests/",
        {
            "grade": str(calificacion.public_id),
            "requested_score": "9",
            "reason": "Se calificó mal una respuesta.",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["status"] == GradeChangeRequest.ESTADO_PENDIENTE
    assert respuesta.data["original_score"] == "6.00"

    calificacion.refresh_from_db()
    assert calificacion.current_score == 6  # RN-05: nada cambia hasta que se aprueba


@pytest.mark.django_db
def test_rf10_rn05_direccion_aprueba_y_solo_cambia_current_score():
    docente, calificacion = _docente_con_nota()
    rol_direccion = RoleFactory(
        name="Dirección", permissions={"notas": "editar", "modificacion_notas": "editar"}
    )
    direccion = UserFactory(role=rol_direccion)

    client = APIClient()
    client.force_authenticate(user=docente)
    creada = client.post(
        "/api/v1/grade-change-requests/",
        {"grade": str(calificacion.public_id), "requested_score": "9", "reason": "Corrección."},
        format="json",
    )
    solicitud_id = creada.data["public_id"]

    client.force_authenticate(user=direccion)
    respuesta = client.post(f"/api/v1/grade-change-requests/{solicitud_id}/approve/")

    assert respuesta.status_code == 200
    assert respuesta.data["status"] == GradeChangeRequest.ESTADO_APROBADA

    calificacion.refresh_from_db()
    assert calificacion.current_score == 9
    assert calificacion.raw_score == 6  # RN-05: el punteo real nunca se toca


@pytest.mark.django_db
def test_rechazar_no_cambia_la_nota():
    docente, calificacion = _docente_con_nota()
    rol_direccion = RoleFactory(
        name="Dirección", permissions={"notas": "editar", "modificacion_notas": "editar"}
    )
    direccion = UserFactory(role=rol_direccion)

    client = APIClient()
    client.force_authenticate(user=docente)
    creada = client.post(
        "/api/v1/grade-change-requests/",
        {"grade": str(calificacion.public_id), "requested_score": "9", "reason": "Corrección."},
        format="json",
    )
    solicitud_id = creada.data["public_id"]

    client.force_authenticate(user=direccion)
    respuesta = client.post(f"/api/v1/grade-change-requests/{solicitud_id}/reject/")

    assert respuesta.status_code == 200
    assert respuesta.data["status"] == GradeChangeRequest.ESTADO_RECHAZADA
    calificacion.refresh_from_db()
    assert calificacion.current_score == 6


@pytest.mark.django_db
def test_solo_direccion_autoriza_modificaciones_acceso_no_autorizado():
    docente, calificacion = _docente_con_nota()

    client = APIClient()
    client.force_authenticate(user=docente)
    creada = client.post(
        "/api/v1/grade-change-requests/",
        {"grade": str(calificacion.public_id), "requested_score": "9", "reason": "Corrección."},
        format="json",
    )
    solicitud_id = creada.data["public_id"]

    respuesta = client.post(f"/api/v1/grade-change-requests/{solicitud_id}/approve/")

    assert respuesta.status_code == 403
    calificacion.refresh_from_db()
    assert calificacion.current_score == 6


@pytest.mark.django_db
def test_familia_nunca_ve_solicitudes_de_modificacion_ajenas_ni_propias():
    """RN-06 (nota 6 de docs/permisos-roles.md): la familia tiene 'ver' en
    el área 'notas' (por eso no da 403), pero el alcance por objeto la
    deja siempre en cero resultados — nunca ve el historial de
    modificaciones, ni siquiera de su propio estudiante."""
    _docente, calificacion = _docente_con_nota()
    rol_familia = RoleFactory(
        name="Padre de familia", permissions={"notas": "ver", "modificacion_notas": "sin_acceso"}
    )
    usuario_familia = UserFactory(role=rol_familia)

    client = APIClient()
    client.force_authenticate(user=usuario_familia)

    respuesta = client.get("/api/v1/grade-change-requests/")
    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 0


@pytest.mark.django_db
def test_familia_no_puede_solicitar_ni_autorizar_modificaciones_acceso_no_autorizado():
    _docente, calificacion = _docente_con_nota()
    rol_familia = RoleFactory(
        name="Padre de familia", permissions={"notas": "ver", "modificacion_notas": "sin_acceso"}
    )
    usuario_familia = UserFactory(role=rol_familia)

    client = APIClient()
    client.force_authenticate(user=usuario_familia)

    respuesta = client.post(
        "/api/v1/grade-change-requests/",
        {"grade": str(calificacion.public_id), "requested_score": "9", "reason": "Pido cambio."},
        format="json",
    )
    assert respuesta.status_code == 403
