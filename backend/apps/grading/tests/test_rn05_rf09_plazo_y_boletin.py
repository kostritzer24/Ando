"""RN-05 con plazo de entrega, RF-09 con boletín congelado al aprobar, en
lote y con las notas pendientes a la vista, y los filtros por los que las
pantallas piden solo lo que muestran."""

from datetime import date

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
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
from apps.core.models import AuditLog
from apps.grading.models import Grade, GradeChangeRequest, ReportCard
from apps.students.tests.factories import EnrollmentFactory

from .factories import ActivityFactory, ActivityTypeFactory, TeacherAssignmentFactory

FUTURO = date(2099, 1, 1)


def _docente():
    return UserFactory(role=RoleFactory(name="Docente", permissions={"notas": "editar"}))


def _direccion():
    return UserFactory(
        role=RoleFactory(
            name="Dirección", permissions={"notas": "editar", "modificacion_notas": "editar"}
        )
    )


def _nota_en_unidad(*, fecha_entrega):
    docente = _docente()
    asignacion = TeacherAssignmentFactory(teacher=docente)
    unidad = GradingUnitFactory(cycle=asignacion.cycle, grades_due_date=fecha_entrega)
    actividad = ActivityFactory(assignment=asignacion, unit=unidad, max_score=10)
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    nota = Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad,
        raw_score=6,
        current_score=6,
        recorded_by=docente,
    )
    client = APIClient()
    client.force_authenticate(user=docente)
    return docente, nota, client


# --- RN-05: corregir dentro del plazo ----------------------------------------


def test_rn05_dentro_del_plazo_el_docente_corrige_su_nota_sin_autorizacion():
    docente, nota, client = _nota_en_unidad(fecha_entrega=FUTURO)

    respuesta = client.post(f"/api/v1/grades/{nota.public_id}/correct/", {"score": "8"})

    assert respuesta.status_code == 200
    assert respuesta.data["current_score"] == "8.00"
    nota.refresh_from_db()
    assert nota.raw_score == 6  # el punteo real se conserva
    registro = AuditLog.objects.get(entity_name="grading.Grade", action="actualizar")
    assert registro.user == docente
    assert registro.old_value == {"current_score": "6.00"}


def test_rn05_despues_del_plazo_la_correccion_directa_es_rechazada():
    _docente_, nota, client = _nota_en_unidad(fecha_entrega=date(2020, 1, 1))

    respuesta = client.post(f"/api/v1/grades/{nota.public_id}/correct/", {"score": "8"})

    assert respuesta.status_code == 400
    assert "solicitá una corrección" in str(respuesta.data)
    nota.refresh_from_db()
    assert nota.current_score == 6


def test_rn05_con_una_solicitud_pendiente_no_se_corrige_directo():
    docente, nota, client = _nota_en_unidad(fecha_entrega=FUTURO)
    GradeChangeRequest.objects.create(
        grade=nota, original_score=6, requested_score=9, reason="x", requested_by=docente
    )

    respuesta = client.post(f"/api/v1/grades/{nota.public_id}/correct/", {"score": "8"})

    assert respuesta.status_code == 400


def test_rn05_un_docente_no_corrige_la_nota_de_otra_asignacion_acceso_no_autorizado():
    _docente_, nota, _client = _nota_en_unidad(fecha_entrega=FUTURO)
    otro = APIClient()
    otro.force_authenticate(user=_docente())

    respuesta = otro.post(f"/api/v1/grades/{nota.public_id}/correct/", {"score": "8"})

    assert respuesta.status_code == 404  # fuera de su alcance: ni la ve


# --- RF-10: el rechazo explica por qué -------------------------------------


def test_rf10_rechazar_sin_motivo_no_se_acepta_y_con_motivo_lo_ve_el_docente():
    docente, nota, client = _nota_en_unidad(fecha_entrega=date(2020, 1, 1))
    solicitud = client.post(
        "/api/v1/grade-change-requests/",
        {"grade": str(nota.public_id), "requested_score": "9", "reason": "Mal sumado."},
        format="json",
    ).data
    direccion = APIClient()
    direccion.force_authenticate(user=_direccion())
    ruta = f"/api/v1/grade-change-requests/{solicitud['public_id']}/reject/"

    sin_motivo = direccion.post(ruta, {}, format="json")
    con_motivo = direccion.post(ruta, {"motivo": "La suma estaba bien."}, format="json")

    assert sin_motivo.status_code == 400
    assert con_motivo.status_code == 200
    bandeja = client.get("/api/v1/grade-change-requests/").data["results"][0]
    assert bandeja["resolution_note"] == "La suma estaba bien."
    assert bandeja["student_name"]
    assert bandeja["current_score"] == "6.00"


def test_rf10_la_bandeja_de_solicitudes_no_hace_una_consulta_por_fila():
    docente = _docente()
    asignacion = TeacherAssignmentFactory(teacher=docente)
    actividad = ActivityFactory(assignment=asignacion, max_score=10)
    for _ in range(12):
        inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
        nota = Grade.objects.create(
            enrollment=inscripcion,
            activity=actividad,
            raw_score=5,
            current_score=5,
            recorded_by=docente,
        )
        GradeChangeRequest.objects.create(
            grade=nota, original_score=5, requested_score=7, reason="x", requested_by=docente
        )
    client = APIClient()
    client.force_authenticate(user=_direccion())

    with CaptureQueriesContext(connection) as consultas:
        respuesta = client.get("/api/v1/grade-change-requests/?status=pendiente")

    assert respuesta.data["count"] == 12
    assert len(consultas) < 12


# --- RF-09: boletín ------------------------------------------------------


def _seccion_con_unidades(cantidad=1):
    ciclo = SchoolCycleFactory(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    seccion = SectionFactory(cycle=ciclo, type=Section.TIPO_ACADEMICA)
    unidades = [
        GradingUnitFactory(
            cycle=ciclo,
            number=numero,
            report_card_enabled_date=date(2020, 1, 1),
        )
        for numero in range(1, cantidad + 1)
    ]
    return ciclo, seccion, unidades


def _examen(asignacion, unidad, inscripcion, punteo):
    actividad = ActivityFactory(
        assignment=asignacion,
        unit=unidad,
        activity_type=ActivityTypeFactory(),
        name=f"Examen U{unidad.number}",
        max_score=100,
    )
    return Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad,
        raw_score=punteo,
        current_score=punteo,
        recorded_by=asignacion.teacher,
    )


def _generar(client, seccion, unidad):
    return client.post(
        "/api/v1/report-cards/generate/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    ).data


def test_rf09_el_boletin_aprobado_no_cambia_si_despues_se_corrige_una_nota():
    ciclo, seccion, (unidad,) = _seccion_con_unidades()
    inscripcion = EnrollmentFactory(section=seccion, cycle=ciclo)
    asignacion = TeacherAssignmentFactory(
        section=seccion, cycle=ciclo, course=CourseFactory(name="Matemática")
    )
    nota = _examen(asignacion, unidad, inscripcion, 85)
    client = APIClient()
    client.force_authenticate(user=_direccion())
    boletin_id = _generar(client, seccion, unidad)[0]["public_id"]

    client.post(f"/api/v1/report-cards/{boletin_id}/approve/")
    Grade.objects.filter(pk=nota.pk).update(current_score=40)

    contenido = ReportCard.objects.get(public_id=boletin_id).contenido
    assert contenido["filas"] == [{"nombre": "Matemática", "notas": ["85"]}]


def test_rn02_rn03_el_boletin_de_la_ultima_unidad_trae_nota_final_y_resultado():
    ciclo, seccion, unidades = _seccion_con_unidades(4)
    inscripcion = EnrollmentFactory(section=seccion, cycle=ciclo)
    asignacion = TeacherAssignmentFactory(
        section=seccion, cycle=ciclo, course=CourseFactory(name="Ciencias")
    )
    for unidad, punteo in zip(unidades, [60, 61, 50, 70], strict=True):
        _examen(asignacion, unidad, inscripcion, punteo)
    client = APIClient()
    client.force_authenticate(user=_direccion())
    boletin_id = _generar(client, seccion, unidades[3])[0]["public_id"]

    client.post(f"/api/v1/report-cards/{boletin_id}/approve/")

    contenido = ReportCard.objects.get(public_id=boletin_id).contenido
    assert contenido["unidades"] == [1, 2, 3, 4]
    assert contenido["filas"] == [
        {"nombre": "Ciencias", "notas": ["60", "61", "50", "70"], "final": 60, "aprobado": True}
    ]


def test_rf09_el_listado_muestra_los_cursos_con_notas_pendientes():
    ciclo, seccion, (unidad,) = _seccion_con_unidades()
    completo = EnrollmentFactory(section=seccion, cycle=ciclo)
    incompleto = EnrollmentFactory(section=seccion, cycle=ciclo)
    asignacion = TeacherAssignmentFactory(
        section=seccion, cycle=ciclo, course=CourseFactory(name="Lenguaje")
    )
    actividad = _examen(asignacion, unidad, completo, 90).activity
    client = APIClient()
    client.force_authenticate(user=_direccion())
    _generar(client, seccion, unidad)

    respuesta = client.get(
        f"/api/v1/report-cards/?section={seccion.public_id}&unit={unidad.public_id}"
    )

    por_inscripcion = {str(b["enrollment"]): b["pendientes"] for b in respuesta.data["results"]}
    assert por_inscripcion[str(completo.public_id)] == []
    assert por_inscripcion[str(incompleto.public_id)] == [
        {"curso": "Lenguaje", "faltan": 1, "diseno_completo": True}
    ]
    assert actividad.max_score == 100


def test_rf09_aprobar_y_publicar_en_lote_informa_quien_quedo_sin_publicar_y_por_que():
    ciclo, seccion, (unidad,) = _seccion_con_unidades()
    EnrollmentFactory(section=seccion, cycle=ciclo, scholarship=ScholarshipFactory())
    EnrollmentFactory(section=seccion, cycle=ciclo)  # sin beca ni pagos: insolvente (RN-09)
    client = APIClient()
    client.force_authenticate(user=_direccion())
    _generar(client, seccion, unidad)
    datos = {"section": str(seccion.public_id), "unit": str(unidad.public_id)}

    aprobados = client.post("/api/v1/report-cards/approve-batch/", datos)
    publicados = client.post("/api/v1/report-cards/publish-batch/", datos)

    assert aprobados.data == {"aprobados": 2}
    assert publicados.data["publicados"] == 1
    assert len(publicados.data["no_publicados"]) == 1
    assert "solvente" in publicados.data["no_publicados"][0]["motivo"]


def test_rf09_solo_direccion_aprueba_en_lote_acceso_no_autorizado():
    ciclo, seccion, (unidad,) = _seccion_con_unidades()
    client = APIClient()
    client.force_authenticate(user=_docente())

    respuesta = client.post(
        "/api/v1/report-cards/approve-batch/",
        {"section": str(seccion.public_id), "unit": str(unidad.public_id)},
    )

    assert respuesta.status_code == 403


# --- Filtros ---------------------------------------------------------------


def test_las_notas_se_filtran_por_actividad_dentro_del_alcance():
    docente = _docente()
    asignacion = TeacherAssignmentFactory(teacher=docente)
    a1 = ActivityFactory(assignment=asignacion, max_score=10, name="A1")
    a2 = ActivityFactory(assignment=asignacion, unit=a1.unit, max_score=10, name="A2")
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    for actividad in (a1, a2):
        Grade.objects.create(
            enrollment=inscripcion,
            activity=actividad,
            raw_score=5,
            current_score=5,
            recorded_by=docente,
        )
    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get(f"/api/v1/grades/?activity={a1.public_id}")
    invalido = client.get("/api/v1/grades/?activity=no-es-un-uuid")

    assert [str(n["activity"]) for n in respuesta.data["results"]] == [str(a1.public_id)]
    assert invalido.status_code == 400


@pytest.mark.parametrize("ruta", ["activities", "grades", "report-cards"])
def test_un_filtro_no_amplia_el_alcance_acceso_no_autorizado(ruta):
    ajena = TeacherAssignmentFactory()
    client = APIClient()
    client.force_authenticate(user=_docente())

    respuesta = client.get(f"/api/v1/{ruta}/?assignment={ajena.public_id}")

    assert respuesta.data["count"] == 0


pytestmark = pytest.mark.django_db
