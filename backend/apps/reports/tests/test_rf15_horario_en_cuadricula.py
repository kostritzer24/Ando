import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import CourseFactory, SectionFactory
from apps.scheduling.models import ScheduleBlock
from apps.scheduling.tests.factories import TeacherAssignmentFactory

pytestmark = pytest.mark.django_db


def _client(nombre_rol="Dirección", nivel="editar"):
    rol = RoleFactory(name=nombre_rol, permissions={"reportes_institucionales": nivel})
    client = APIClient()
    client.force_authenticate(user=UserFactory(role=rol))
    return client


def _asignacion_con_bloque(seccion, curso, dia, periodo):
    asignacion = TeacherAssignmentFactory(
        section=seccion, cycle=seccion.cycle, course=CourseFactory(name=curso)
    )
    ScheduleBlock.objects.create(assignment=asignacion, day_of_week=dia, period_number=periodo)
    return asignacion


def test_rf15_horario_de_un_grado_en_cuadricula():
    seccion = SectionFactory()
    _asignacion_con_bloque(seccion, "Matemática", "lunes", 1)
    _asignacion_con_bloque(seccion, "Lenguaje", "martes", 5)

    respuesta = _client().get(f"/api/v1/reports/schedule-grid/?section={seccion.public_id}")

    assert respuesta.status_code == 200
    periodos = {p["numero"]: p for p in respuesta.data["periodos"]}
    assert list(periodos) == [1, 2, 3, 4, 5, 6]
    assert periodos[1]["celdas"]["lunes"]["curso"] == "Matemática"
    assert periodos[5]["celdas"]["martes"]["curso"] == "Lenguaje"
    assert periodos[2]["celdas"]["lunes"] is None


def test_rf15_horario_de_una_persona_en_cuadricula_y_en_pdf():
    seccion = SectionFactory()
    asignacion = _asignacion_con_bloque(seccion, "Matemática", "lunes", 2)

    cliente = _client()
    url = f"/api/v1/reports/schedule-grid/?teacher={asignacion.teacher.public_id}"
    json_ = cliente.get(url)
    pdf = cliente.get(url + "&export=pdf")

    assert json_.data["periodos"][1]["celdas"]["lunes"]["curso"] == "Matemática"
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"


def test_rf15_el_horario_de_un_taller_muestra_la_franja_de_la_tarde():
    taller = SectionFactory(type="taller", grade="Panadería")
    asignacion = TeacherAssignmentFactory(
        section=taller, cycle=taller.cycle, course=CourseFactory(name="Panadería", type="taller")
    )
    ScheduleBlock.objects.create(assignment=asignacion, day_of_week="lunes", period_number=7)

    respuesta = _client().get(f"/api/v1/reports/schedule-grid/?section={taller.public_id}")

    assert [p["numero"] for p in respuesta.data["periodos"]] == [7, 8, 9, 10, 11]


def test_rf15_pide_una_seccion_o_una_persona():
    assert _client().get("/api/v1/reports/schedule-grid/").status_code == 400


def test_rf15_horario_en_cuadricula_acceso_no_autorizado():
    cliente = _client("Docente", "sin_acceso")
    assert cliente.get("/api/v1/reports/schedule-grid/?section=x").status_code == 403
