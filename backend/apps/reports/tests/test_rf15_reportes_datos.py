from decimal import Decimal

import pytest
from django.core.files.base import ContentFile
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.attendance.models import Attendance
from apps.attendance.tests.factories import AttendanceFactory
from apps.catalog.models import Section
from apps.catalog.tests.factories import (
    DocumentTypeFactory,
    GradingUnitFactory,
    ScholarshipFactory,
    SectionFactory,
)
from apps.documents.models import IssuedDocument
from apps.grading.models import Grade, GradeChangeRequest
from apps.grading.tests.factories import (
    ActivityFactory,
    ActivityTypeFactory,
    TeacherAssignmentFactory,
)
from apps.scheduling.models import ScheduleBlock
from apps.students.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


def _direccion():
    rol = RoleFactory(
        name="Dirección",
        permissions={"reportes_institucionales": "editar", "pagos_solvencia": "editar"},
    )
    return UserFactory(role=rol)


def test_rf15_consolidado_de_notas_usa_la_misma_nota_de_unidad_que_la_captura():
    asignacion = TeacherAssignmentFactory()
    for numero in range(1, 5):
        GradingUnitFactory(cycle=asignacion.cycle, number=numero)
    unidad_1 = asignacion.cycle.units.get(number=1)
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    actividad = ActivityFactory(
        assignment=asignacion, unit=unidad_1, activity_type=ActivityTypeFactory(), max_score=100
    )
    Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad,
        raw_score=70,
        current_score=70,
        recorded_by=asignacion.teacher,
    )

    client = APIClient()
    client.force_authenticate(user=_direccion())
    respuesta = client.get(
        "/api/v1/reports/grades-summary/",
        {"cycle": str(asignacion.cycle.public_id), "section": str(asignacion.section.public_id)},
    )

    assert respuesta.status_code == 200
    fila = next(f for f in respuesta.data["results"] if f["course"] == asignacion.course.name)
    assert fila["unit_1_score"] == Decimal("70.00")
    assert fila["final_score"] is not None


def test_rf15_reporte_de_asistencia_cuenta_por_estado():
    inscripcion = EnrollmentFactory()
    AttendanceFactory(enrollment=inscripcion, date="2026-01-13", status=Attendance.ESTADO_PRESENTE)
    AttendanceFactory(enrollment=inscripcion, date="2026-01-14", status=Attendance.ESTADO_TARDE)
    AttendanceFactory(enrollment=inscripcion, date="2026-01-15", status=Attendance.ESTADO_AUSENTE)

    client = APIClient()
    client.force_authenticate(user=_direccion())
    respuesta = client.get(
        "/api/v1/reports/attendance/", {"section": str(inscripcion.section.public_id)}
    )

    fila = respuesta.data["results"][0]
    assert fila["presente"] == 1
    assert fila["tarde"] == 1
    assert fila["ausente"] == 1
    assert fila["justificado"] == 0


def test_rf15_reporte_de_insolventes_excluye_a_los_becados():
    seccion = SectionFactory(type=Section.TIPO_ACADEMICA)
    beca = ScholarshipFactory()
    becado = EnrollmentFactory(section=seccion, cycle=seccion.cycle, scholarship=beca)
    sin_pagos = EnrollmentFactory(section=seccion, cycle=seccion.cycle)

    client = APIClient()
    client.force_authenticate(user=_direccion())
    respuesta = client.get(
        "/api/v1/reports/insolvent-students/", {"section": str(seccion.public_id)}
    )

    codigos = {f["student_code"] for f in respuesta.data["results"]}
    assert sin_pagos.student.internal_code in codigos
    assert becado.student.internal_code not in codigos


def test_rf15_reporte_de_horarios_lista_los_bloques_activos():
    asignacion = TeacherAssignmentFactory()
    ScheduleBlock.objects.create(assignment=asignacion, day_of_week="lunes", period_number=1)

    client = APIClient()
    client.force_authenticate(user=_direccion())
    respuesta = client.get(
        "/api/v1/reports/schedules/", {"section": str(asignacion.section.public_id)}
    )

    assert respuesta.data["results"] == [
        {
            "section": str(asignacion.section),
            "course": asignacion.course.name,
            "teacher": asignacion.teacher.nombre_completo(),
            "day_of_week": "lunes",
            "period_number": 1,
        }
    ]


def test_rf15_reporte_de_estudiantes_inscritos():
    inscripcion = EnrollmentFactory()

    client = APIClient()
    client.force_authenticate(user=_direccion())
    respuesta = client.get(
        "/api/v1/reports/enrolled-students/", {"cycle": str(inscripcion.cycle.public_id)}
    )

    assert respuesta.data["results"][0]["student_code"] == inscripcion.student.internal_code
    assert respuesta.data["results"][0]["status"] == "Activo"


def test_rf15_historial_de_modificaciones_de_notas():
    actividad = ActivityFactory(max_score=100)
    inscripcion = EnrollmentFactory(
        section=actividad.assignment.section, cycle=actividad.assignment.cycle
    )
    calificacion = Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad,
        raw_score=60,
        current_score=60,
        recorded_by=actividad.assignment.teacher,
    )
    GradeChangeRequest.objects.create(
        grade=calificacion,
        original_score=60,
        requested_score=75,
        reason="Error de digitación.",
        requested_by=actividad.assignment.teacher,
    )

    client = APIClient()
    client.force_authenticate(user=_direccion())
    respuesta = client.get("/api/v1/reports/grade-change-history/")

    fila = respuesta.data["results"][0]
    assert fila["original_score"] == Decimal("60.00")
    assert fila["requested_score"] == Decimal("75.00")
    assert fila["status"] == "Pendiente"


def test_rf15_reporte_de_accesos_solo_incluye_a_las_familias():
    from apps.core.services import registrar_acceso

    rol_familia = RoleFactory(name="Padre de familia", permissions={})
    familia = UserFactory(role=rol_familia, username="familia.reportes")
    rol_docente = RoleFactory(name="Docente", permissions={})
    docente = UserFactory(role=rol_docente, username="docente.reportes")
    registrar_acceso(usuario=familia, pantalla="/portal")
    registrar_acceso(usuario=docente, pantalla="/operativo")

    client = APIClient()
    client.force_authenticate(user=_direccion())
    respuesta = client.get("/api/v1/reports/family-access/")

    usuarios = {f["user"] for f in respuesta.data["results"]}
    assert usuarios == {"familia.reportes"}


def test_rf15_reporte_de_documentos_emitidos():
    tipo = DocumentTypeFactory()
    inscripcion = EnrollmentFactory()
    IssuedDocument.objects.create(
        document_type=tipo,
        enrollment=inscripcion,
        verification_code="ABCDEF123456",
        issued_by=_direccion(),
        file=ContentFile(b"%PDF-1.4 contenido de prueba", name="prueba.pdf"),
    )

    client = APIClient()
    client.force_authenticate(user=_direccion())
    respuesta = client.get(
        "/api/v1/reports/issued-documents/", {"section": str(inscripcion.section.public_id)}
    )

    assert respuesta.data["results"][0]["student_code"] == inscripcion.student.internal_code
    assert respuesta.data["results"][0]["document_type"] == tipo.name


def test_rf15_el_reporte_se_puede_descargar_en_pdf():
    EnrollmentFactory()
    client = APIClient()
    client.force_authenticate(user=_direccion())

    respuesta = client.get("/api/v1/reports/enrolled-students/", {"export": "pdf"})

    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta.content[:4] == b"%PDF"
