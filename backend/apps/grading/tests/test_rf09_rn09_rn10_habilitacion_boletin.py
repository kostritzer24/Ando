from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import Section
from apps.catalog.tests.factories import (
    CourseFactory,
    GradingUnitFactory,
    ScholarshipFactory,
    SchoolCycleFactory,
    SectionFactory,
)
from apps.grading.models import Activity, Grade, ReportCard
from apps.grading.tests.factories import ActivityTypeFactory, TeacherAssignmentFactory
from apps.students.services.link import vincular_encargado_estudiante
from apps.students.tests.factories import EnrollmentFactory, GuardianFactory, StudentFactory

pytestmark = pytest.mark.django_db


def _direccion():
    rol = RoleFactory(name="Dirección", permissions={"notas": "editar"})
    return UserFactory(role=rol)


def _seccion_con_ciclo(**kwargs_unidad):
    ciclo = SchoolCycleFactory(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    seccion = SectionFactory(cycle=ciclo, type=Section.TIPO_ACADEMICA)
    unidad = GradingUnitFactory(
        cycle=ciclo,
        number=1,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 2, 28),
        grades_due_date=date(2026, 3, 15),
        **kwargs_unidad,
    )
    return ciclo, seccion, unidad


def test_rf09_direccion_genera_un_boletin_por_cada_inscripcion_activa_de_la_seccion():
    ciclo, seccion, unidad = _seccion_con_ciclo(report_card_enabled_date=date(2099, 1, 1))
    EnrollmentFactory(section=seccion, cycle=ciclo)
    EnrollmentFactory(section=seccion, cycle=ciclo)
    otra_seccion = SectionFactory(cycle=ciclo, type=Section.TIPO_ACADEMICA)
    EnrollmentFactory(section=otra_seccion, cycle=ciclo)  # no debe entrar.

    client = APIClient()
    client.force_authenticate(user=_direccion())

    respuesta = client.post(
        "/api/v1/report-cards/generate/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    )

    assert respuesta.status_code == 201
    assert len(respuesta.data) == 2
    assert ReportCard.objects.filter(unit=unidad).count() == 2
    assert all(rc["status"] == "borrador" for rc in respuesta.data)


def test_rf09_generar_de_nuevo_no_reinicia_un_boletin_ya_aprobado():
    ciclo, seccion, unidad = _seccion_con_ciclo(report_card_enabled_date=date(2020, 1, 1))
    beca = ScholarshipFactory()
    EnrollmentFactory(section=seccion, cycle=ciclo, scholarship=beca)
    client = APIClient()
    client.force_authenticate(user=_direccion())

    primera = client.post(
        "/api/v1/report-cards/generate/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    )
    boletin_id = primera.data[0]["public_id"]
    client.post(f"/api/v1/report-cards/{boletin_id}/approve/")

    client.post(
        "/api/v1/report-cards/generate/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    )

    boletin = ReportCard.objects.get(public_id=boletin_id)
    assert boletin.status == ReportCard.ESTADO_APROBADO


def test_rf09_docente_no_puede_generar_boletines_acceso_no_autorizado():
    """`docs/api.md`: generar/aprobar/publicar boletines es DIR (E), más
    estricto que el E que un docente tiene en el área "notas"."""
    ciclo, seccion, unidad = _seccion_con_ciclo(report_card_enabled_date=date(2099, 1, 1))
    rol = RoleFactory(name="Docente", permissions={"notas": "editar"})
    docente = UserFactory(role=rol)
    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/report-cards/generate/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    )

    assert respuesta.status_code == 403


def test_rf09_no_se_puede_aprobar_dos_veces_el_mismo_boletin():
    ciclo, seccion, unidad = _seccion_con_ciclo(report_card_enabled_date=date(2099, 1, 1))
    EnrollmentFactory(section=seccion, cycle=ciclo)
    client = APIClient()
    client.force_authenticate(user=_direccion())
    generado = client.post(
        "/api/v1/report-cards/generate/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    )
    boletin_id = generado.data[0]["public_id"]

    primera = client.post(f"/api/v1/report-cards/{boletin_id}/approve/")
    segunda = client.post(f"/api/v1/report-cards/{boletin_id}/approve/")

    assert primera.status_code == 200
    assert segunda.status_code == 400


def test_rn10_no_se_puede_publicar_antes_del_plazo_aunque_este_solvente():
    ciclo, seccion, unidad = _seccion_con_ciclo(report_card_enabled_date=date(2099, 1, 1))
    beca = ScholarshipFactory()
    EnrollmentFactory(section=seccion, cycle=ciclo, scholarship=beca)
    client = APIClient()
    client.force_authenticate(user=_direccion())
    generado = client.post(
        "/api/v1/report-cards/generate/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    )
    boletin_id = generado.data[0]["public_id"]
    client.post(f"/api/v1/report-cards/{boletin_id}/approve/")

    respuesta = client.post(f"/api/v1/report-cards/{boletin_id}/publish/")

    assert respuesta.status_code == 400
    assert "plazo" in str(respuesta.data).lower()


def test_rn09_no_se_puede_publicar_si_el_estudiante_no_esta_solvente():
    ciclo, seccion, unidad = _seccion_con_ciclo(report_card_enabled_date=date(2020, 1, 1))
    EnrollmentFactory(section=seccion, cycle=ciclo)  # sin beca, sin pagos.
    client = APIClient()
    client.force_authenticate(user=_direccion())
    generado = client.post(
        "/api/v1/report-cards/generate/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    )
    boletin_id = generado.data[0]["public_id"]
    client.post(f"/api/v1/report-cards/{boletin_id}/approve/")

    respuesta = client.post(f"/api/v1/report-cards/{boletin_id}/publish/")

    assert respuesta.status_code == 400
    assert "solvente" in str(respuesta.data).lower()


def test_rf09_se_publica_cuando_se_cumple_el_plazo_y_esta_solvente_y_la_familia_lo_ve():
    ciclo, seccion, unidad = _seccion_con_ciclo(report_card_enabled_date=date(2020, 1, 1))
    beca = ScholarshipFactory()
    rol_familia = RoleFactory(name="Padre de familia", permissions={"notas": "ver"})
    usuario_familia = UserFactory(role=rol_familia)
    encargado = GuardianFactory(user=usuario_familia)
    mi_hijo = StudentFactory(internal_code="ES030")
    vincular_encargado_estudiante(guardian=encargado, student=mi_hijo, relationship="Madre")
    EnrollmentFactory(student=mi_hijo, section=seccion, cycle=ciclo, scholarship=beca)

    client = APIClient()
    client.force_authenticate(user=_direccion())
    generado = client.post(
        "/api/v1/report-cards/generate/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    )
    boletin_id = generado.data[0]["public_id"]
    client.post(f"/api/v1/report-cards/{boletin_id}/approve/")

    client_familia = APIClient()
    client_familia.force_authenticate(user=usuario_familia)
    antes = client_familia.get("/api/v1/report-cards/")
    assert antes.data["count"] == 0  # todavía en "aprobado", no publicado.

    respuesta = client.post(f"/api/v1/report-cards/{boletin_id}/publish/")
    assert respuesta.status_code == 200
    assert respuesta.data["status"] == "publicado"

    despues = client_familia.get("/api/v1/report-cards/")
    assert despues.data["count"] == 1


def test_rf34_no_se_puede_descargar_un_boletin_que_no_esta_publicado():
    ciclo, seccion, unidad = _seccion_con_ciclo(report_card_enabled_date=date(2099, 1, 1))
    EnrollmentFactory(section=seccion, cycle=ciclo)
    client = APIClient()
    client.force_authenticate(user=_direccion())
    generado = client.post(
        "/api/v1/report-cards/generate/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    )
    boletin_id = generado.data[0]["public_id"]

    respuesta = client.get(f"/api/v1/report-cards/{boletin_id}/download/")

    assert respuesta.status_code == 400
    assert "publicado" in str(respuesta.data).lower()


def test_rf34_la_familia_descarga_el_pdf_de_un_boletin_publicado_con_la_nota_por_curso():
    ciclo, seccion, unidad = _seccion_con_ciclo(report_card_enabled_date=date(2020, 1, 1))
    beca = ScholarshipFactory()
    rol_familia = RoleFactory(name="Padre de familia", permissions={"notas": "ver"})
    usuario_familia = UserFactory(role=rol_familia)
    encargado = GuardianFactory(user=usuario_familia)
    mi_hijo = StudentFactory(internal_code="ES031")
    vincular_encargado_estudiante(guardian=encargado, student=mi_hijo, relationship="Madre")
    inscripcion = EnrollmentFactory(student=mi_hijo, section=seccion, cycle=ciclo, scholarship=beca)

    asignacion = TeacherAssignmentFactory(
        section=seccion, cycle=ciclo, course=CourseFactory(name="Matemática")
    )
    actividad = Activity.objects.create(
        assignment=asignacion,
        unit=unidad,
        activity_type=ActivityTypeFactory(),
        name="Examen",
        max_score=100,
        due_date=unidad.end_date,
    )
    Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad,
        raw_score=85,
        current_score=85,
        recorded_by=asignacion.teacher,
    )

    client = APIClient()
    client.force_authenticate(user=_direccion())
    generado = client.post(
        "/api/v1/report-cards/generate/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    )
    boletin_id = generado.data[0]["public_id"]
    client.post(f"/api/v1/report-cards/{boletin_id}/approve/")
    client.post(f"/api/v1/report-cards/{boletin_id}/publish/")

    client_familia = APIClient()
    client_familia.force_authenticate(user=usuario_familia)
    respuesta = client_familia.get(f"/api/v1/report-cards/{boletin_id}/download/")

    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta.content[:4] == b"%PDF"
