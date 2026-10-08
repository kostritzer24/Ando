import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.students.models import GuardianStudentLink

from .factories import GuardianFactory, StudentFactory


@pytest.mark.django_db
def test_rf04_direccion_vincula_un_encargado_con_un_estudiante():
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)
    encargado = GuardianFactory()
    estudiante = StudentFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        f"/api/v1/guardians/{encargado.public_id}/link-student/",
        {"student": str(estudiante.public_id), "relationship": "Madre", "is_primary": True},
        format="json",
    )

    assert respuesta.status_code == 201
    assert GuardianStudentLink.objects.filter(guardian=encargado, student=estudiante).exists()


@pytest.mark.django_db
def test_no_se_puede_crear_un_encargado_a_partir_de_un_usuario_con_otro_rol():
    rol_direccion = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol_direccion)
    rol_docente = RoleFactory(name="Docente")
    usuario_docente = UserFactory(role=rol_docente)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/guardians/",
        {"user": str(usuario_docente.public_id), "full_name": "No debería crearse"},
        format="json",
    )

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_adr0002_un_estudiante_puede_tener_mas_de_un_encargado():
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)
    estudiante = StudentFactory()
    madre = GuardianFactory(full_name="Madre de prueba")
    padre = GuardianFactory(full_name="Padre de prueba")

    client = APIClient()
    client.force_authenticate(user=direccion)

    for encargado, parentesco in [(madre, "Madre"), (padre, "Padre")]:
        respuesta = client.post(
            f"/api/v1/guardians/{encargado.public_id}/link-student/",
            {"student": str(estudiante.public_id), "relationship": parentesco},
            format="json",
        )
        assert respuesta.status_code == 201

    assert estudiante.guardian_links.filter(is_active=True).count() == 2


@pytest.mark.django_db
def test_rf04_no_se_puede_repetir_el_mismo_vinculo():
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)
    encargado = GuardianFactory()
    estudiante = StudentFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    datos = {"student": str(estudiante.public_id), "relationship": "Madre"}
    primera = client.post(
        f"/api/v1/guardians/{encargado.public_id}/link-student/", datos, format="json"
    )
    segunda = client.post(
        f"/api/v1/guardians/{encargado.public_id}/link-student/", datos, format="json"
    )

    assert primera.status_code == 201
    assert segunda.status_code == 400


@pytest.mark.django_db
def test_rf04_consultar_los_vinculos_de_un_encargado():
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)
    encargado = GuardianFactory()
    hijo = StudentFactory(internal_code="ES010", first_name="Ana", last_name="Pérez")
    hija_desvinculada = StudentFactory(internal_code="ES011")

    client = APIClient()
    client.force_authenticate(user=direccion)
    client.post(
        f"/api/v1/guardians/{encargado.public_id}/link-student/",
        {"student": str(hijo.public_id), "relationship": "Madre", "is_primary": True},
        format="json",
    )
    client.post(
        f"/api/v1/guardians/{encargado.public_id}/link-student/",
        {"student": str(hija_desvinculada.public_id), "relationship": "Madre"},
        format="json",
    )
    client.delete(
        f"/api/v1/guardians/{encargado.public_id}/link-student/{hija_desvinculada.public_id}/"
    )

    respuesta = client.get(f"/api/v1/guardians/{encargado.public_id}/link-student/")

    assert respuesta.status_code == 200
    assert len(respuesta.data) == 1
    assert respuesta.data[0]["student_name"] == "Ana Pérez"
    assert respuesta.data[0]["relationship"] == "Madre"
    assert respuesta.data[0]["is_primary"] is True


@pytest.mark.django_db
def test_rf04_desvincular_es_baja_logica():
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)
    encargado = GuardianFactory()
    estudiante = StudentFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)
    client.post(
        f"/api/v1/guardians/{encargado.public_id}/link-student/",
        {"student": str(estudiante.public_id), "relationship": "Madre"},
        format="json",
    )

    respuesta = client.delete(
        f"/api/v1/guardians/{encargado.public_id}/link-student/{estudiante.public_id}/"
    )

    assert respuesta.status_code == 204
    vinculo = GuardianStudentLink.objects.get(guardian=encargado, student=estudiante)
    assert vinculo.is_active is False


@pytest.mark.django_db
def test_rf04_tallerista_no_puede_vincular_encargados_acceso_no_autorizado():
    rol = RoleFactory(name="Tallerista", permissions={"estudiantes_encargados": "ver"})
    tallerista = UserFactory(role=rol)
    encargado = GuardianFactory()
    estudiante = StudentFactory()

    client = APIClient()
    client.force_authenticate(user=tallerista)

    respuesta = client.post(
        f"/api/v1/guardians/{encargado.public_id}/link-student/",
        {"student": str(estudiante.public_id), "relationship": "Madre"},
        format="json",
    )

    assert respuesta.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize("recurso", ["students", "guardians"])
def test_hu02_delete_da_de_baja_logica_y_no_borra_la_fila(recurso):
    """Hallazgo B-018: DELETE borraba de verdad estudiantes y encargados."""
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)
    registro = StudentFactory() if recurso == "students" else GuardianFactory()
    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.delete(f"/api/v1/{recurso}/{registro.public_id}/")

    assert respuesta.status_code == 204
    registro.refresh_from_db()
    assert registro.is_active is False


@pytest.mark.django_db
def test_rf03_dar_de_baja_a_un_estudiante_retira_sus_inscripciones_y_lo_saca_de_las_listas():
    """Decisión del dueño (oct 2026) / hallazgo D-016: la baja conserva todo el
    historial, retira las inscripciones activas y deja registro en la bitácora."""
    from apps.core.models import AuditLog
    from apps.students.models import Enrollment
    from apps.students.tests.factories import EnrollmentFactory

    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    direccion = UserFactory(role=rol)
    inscripcion = EnrollmentFactory()
    estudiante = inscripcion.student
    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.delete(f"/api/v1/students/{estudiante.public_id}/")

    assert respuesta.status_code == 204
    inscripcion.refresh_from_db()
    assert inscripcion.status == Enrollment.ESTADO_RETIRADO
    listado = client.get("/api/v1/students/")
    assert estudiante.public_id.hex not in str(listado.data).replace("-", "")
    assert client.get(f"/api/v1/students/{estudiante.public_id}/").status_code == 200
    assert AuditLog.objects.filter(entity_name="students.Student", action="eliminar").exists()
