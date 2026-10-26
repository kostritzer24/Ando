"""RF-39 (repartir puntos) y RF-40 (promediar unidad), con RN-20 a RN-22."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import GradingUnitFactory
from apps.core.models import AuditLog
from apps.grading.models import Activity, Grade, ReportCard, UnitAveraging
from apps.grading.selectors.avance import pendientes_por_inscripcion
from apps.grading.services.consolidado import consolidado_de_notas
from apps.grading.services.grade import nota_de_unidad
from apps.grading.services.report_card import contenido_boletin
from apps.reports.selectors.grades_summary import resumen_notas
from apps.students.services.link import vincular_encargado_estudiante
from apps.students.tests.factories import EnrollmentFactory, GuardianFactory

from .factories import ActivityFactory, ActivityTypeFactory, TeacherAssignmentFactory

pytestmark = pytest.mark.django_db


def _docente():
    return UserFactory(role=RoleFactory(name="Docente", permissions={"notas": "editar"}))


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


def _unidad_de(docente):
    asignacion = TeacherAssignmentFactory(teacher=docente)
    unidad = GradingUnitFactory(cycle=asignacion.cycle, number=1)
    return asignacion, unidad


def _actividad(asignacion, unidad, nombre, max_score):
    return ActivityFactory(
        assignment=asignacion,
        unit=unidad,
        activity_type=ActivityTypeFactory(),
        name=nombre,
        max_score=max_score,
    )


def _calificar(inscripcion, actividad, punteo):
    return Grade.objects.create(
        enrollment=inscripcion,
        activity=actividad,
        raw_score=punteo,
        current_score=punteo,
        recorded_by=actividad.assignment.teacher,
    )


def _cuerpo(asignacion, unidad, **extra):
    return {"assignment": str(asignacion.public_id), "unit": str(unidad.public_id), **extra}


# --- RF-39: repartir puntos -------------------------------------------------


def test_rf39_se_crea_una_actividad_sin_punteo_maximo_todavia():
    docente = _docente()
    asignacion, unidad = _unidad_de(docente)

    respuesta = _cliente(docente).post(
        "/api/v1/activities/",
        {
            **_cuerpo(asignacion, unidad),
            "activity_type": str(ActivityTypeFactory().public_id),
            "name": "Proyecto",
            "due_date": "2026-02-10",
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.data["max_score"] is None


def test_rf39_rn20_reparte_100_puntos_en_partes_iguales_y_queda_en_bitacora():
    docente = _docente()
    asignacion, unidad = _unidad_de(docente)
    for nombre in ("A", "B", "C"):
        _actividad(asignacion, unidad, nombre, None)

    respuesta = _cliente(docente).post(
        "/api/v1/activities/distribute/", _cuerpo(asignacion, unidad)
    )

    assert respuesta.status_code == 200
    maximos = sorted(Activity.objects.values_list("max_score", flat=True))
    assert maximos == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
    assert sum(maximos) == 100
    assert AuditLog.objects.filter(entity_name="grading.Activity", action="actualizar").count() == 3


def test_rf39_rn20_las_actividades_calificadas_conservan_su_punteo():
    docente = _docente()
    asignacion, unidad = _unidad_de(docente)
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    calificada = _actividad(asignacion, unidad, "Corto", Decimal("10"))
    _calificar(inscripcion, calificada, Decimal("8"))
    libres = [_actividad(asignacion, unidad, n, Decimal("5")) for n in ("A", "B")]

    _cliente(docente).post("/api/v1/activities/distribute/", _cuerpo(asignacion, unidad))

    calificada.refresh_from_db()
    assert calificada.max_score == Decimal("10")
    for actividad in libres:
        actividad.refresh_from_db()
        assert actividad.max_score == Decimal("45")


def test_rf39_un_docente_no_reparte_en_una_asignacion_ajena_acceso_no_autorizado():
    asignacion, unidad = _unidad_de(_docente())
    _actividad(asignacion, unidad, "A", None)

    respuesta = _cliente(_docente()).post(
        "/api/v1/activities/distribute/", _cuerpo(asignacion, unidad)
    )

    assert respuesta.status_code == 403
    assert Activity.objects.get().max_score is None


def test_rf39_sin_actividades_libres_el_reparto_se_rechaza():
    docente = _docente()
    asignacion, unidad = _unidad_de(docente)

    respuesta = _cliente(docente).post(
        "/api/v1/activities/distribute/", _cuerpo(asignacion, unidad)
    )

    assert respuesta.status_code == 400


# --- RN-21: sin punteo máximo no se califica --------------------------------


def test_rn21_no_se_califica_una_actividad_sin_punteo_maximo():
    docente = _docente()
    asignacion, unidad = _unidad_de(docente)
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    actividad = _actividad(asignacion, unidad, "Proyecto", None)

    respuesta = _cliente(docente).post(
        "/api/v1/grades/",
        {
            "enrollment": str(inscripcion.public_id),
            "activity": str(actividad.public_id),
            "raw_score": "8",
        },
    )

    assert respuesta.status_code == 400
    assert Grade.objects.count() == 0


def test_rn21_no_se_genera_la_plantilla_con_actividades_sin_punteo_maximo():
    docente = _docente()
    asignacion, unidad = _unidad_de(docente)
    _actividad(asignacion, unidad, "Proyecto", None)

    respuesta = _cliente(docente).get(
        f"/api/v1/grades/template/{asignacion.public_id}/{unidad.public_id}/"
    )

    assert respuesta.status_code == 400


# --- RF-40 / RN-22: promediar la unidad -------------------------------------


def _unidad_incompleta():
    """Una unidad que solo llegó a 70 puntos: 9/10 y 40/60."""
    docente = _docente()
    asignacion, unidad = _unidad_de(docente)
    inscripcion = EnrollmentFactory(section=asignacion.section, cycle=asignacion.cycle)
    corto = _actividad(asignacion, unidad, "Corto", Decimal("10"))
    examen = _actividad(asignacion, unidad, "Examen", Decimal("60"))
    _calificar(inscripcion, corto, Decimal("9"))
    _calificar(inscripcion, examen, Decimal("40"))
    return docente, asignacion, unidad, inscripcion


def test_rf40_rn22_promediar_lleva_la_nota_a_100_sin_tocar_los_punteos():
    docente, asignacion, unidad, inscripcion = _unidad_incompleta()
    assert nota_de_unidad(enrollment=inscripcion, unit=unidad, assignment=asignacion) == 49

    respuesta = _cliente(docente).post(
        "/api/v1/activities/average/", _cuerpo(asignacion, unidad, averaged=True)
    )

    assert respuesta.status_code == 200
    assert respuesta.data["promediada"] is True
    assert Decimal(respuesta.data["puntos_evaluados"]) == 70
    assert nota_de_unidad(enrollment=inscripcion, unit=unidad, assignment=asignacion) == Decimal(
        "70.00"
    )
    # RN-05/RN-06: la nota real y la vigente siguen tal cual.
    assert sorted(Grade.objects.values_list("raw_score", "current_score")) == [
        (Decimal("9"), Decimal("9")),
        (Decimal("40"), Decimal("40")),
    ]
    assert AuditLog.objects.filter(entity_name="grading.UnitAveraging").count() == 1


def test_rf40_quitar_el_promedio_vuelve_a_la_suma():
    docente, asignacion, unidad, inscripcion = _unidad_incompleta()
    client = _cliente(docente)
    client.post("/api/v1/activities/average/", _cuerpo(asignacion, unidad, averaged=True))

    respuesta = client.post(
        "/api/v1/activities/average/", _cuerpo(asignacion, unidad, averaged=False)
    )

    assert respuesta.data["promediada"] is False
    assert nota_de_unidad(enrollment=inscripcion, unit=unidad, assignment=asignacion) == 49


def test_rf40_antes_de_promediar_da_de_baja_las_actividades_que_ya_no_se_haran():
    docente, asignacion, unidad, inscripcion = _unidad_incompleta()
    pendiente = _actividad(asignacion, unidad, "Proyecto", Decimal("30"))

    respuesta = _cliente(docente).post(
        "/api/v1/activities/average/",
        _cuerpo(asignacion, unidad, averaged=True, deactivate=[str(pendiente.public_id)]),
        format="json",
    )

    assert respuesta.status_code == 200
    pendiente.refresh_from_db()
    assert pendiente.is_active is False
    assert Decimal(respuesta.data["puntos_evaluados"]) == 70


def test_rf40_no_se_da_de_baja_una_actividad_calificada_al_promediar():
    docente, asignacion, unidad, _ = _unidad_incompleta()
    calificada = Activity.objects.get(name="Corto")

    respuesta = _cliente(docente).post(
        "/api/v1/activities/average/",
        _cuerpo(asignacion, unidad, averaged=True, deactivate=[str(calificada.public_id)]),
        format="json",
    )

    assert respuesta.status_code == 400
    assert not UnitAveraging.objects.exists()


def test_rf40_un_docente_no_promedia_una_asignacion_ajena_acceso_no_autorizado():
    _, asignacion, unidad, _ = _unidad_incompleta()

    respuesta = _cliente(_docente()).post(
        "/api/v1/activities/average/", _cuerpo(asignacion, unidad, averaged=True)
    )
    estado = _cliente(_docente()).get(
        "/api/v1/activities/unit-status/", _cuerpo(asignacion, unidad)
    )

    assert respuesta.status_code == 403
    assert estado.status_code == 403
    assert not UnitAveraging.objects.exists()


def test_rn22_con_un_boletin_aprobado_el_promedio_ya_no_cambia():
    docente, asignacion, unidad, inscripcion = _unidad_incompleta()
    ReportCard.objects.create(
        enrollment=inscripcion,
        unit=unidad,
        status=ReportCard.ESTADO_APROBADO,
        generated_by=docente,
    )

    estado = _cliente(docente).get("/api/v1/activities/unit-status/", _cuerpo(asignacion, unidad))
    respuesta = _cliente(docente).post(
        "/api/v1/activities/average/", _cuerpo(asignacion, unidad, averaged=True)
    )

    assert estado.data["bloqueada"] is True
    assert respuesta.status_code == 400
    assert not UnitAveraging.objects.exists()


def test_rn22_todos_los_consumidores_usan_la_nota_promediada():
    docente, asignacion, unidad, inscripcion = _unidad_incompleta()
    _cliente(docente).post(
        "/api/v1/activities/average/", _cuerpo(asignacion, unidad, averaged=True)
    )
    boletin = ReportCard.objects.create(enrollment=inscripcion, unit=unidad, generated_by=docente)

    cuadro = contenido_boletin(boletin)["cursos"][0]
    assert Decimal(cuadro["unidades"][0]) == Decimal("70")
    consolidado = consolidado_de_notas(inscripcion.student)["anios"][0]["cursos"][0]
    assert Decimal(consolidado["unidades"][0]) == Decimal("70")
    fila_reporte = resumen_notas(section_id=str(asignacion.section.public_id))[0]
    assert fila_reporte["unit_1_score"] == Decimal("70.00")
    # La unidad promediada no cuenta como "suma 70 de 100" para el boletín.
    assert pendientes_por_inscripcion(inscripciones=[inscripcion], unit=unidad) == {}


def test_rn22_el_portal_recibe_la_nota_calculada_y_la_familia_solo_ve_la_nota():
    docente, asignacion, unidad, inscripcion = _unidad_incompleta()
    _cliente(docente).post(
        "/api/v1/activities/average/", _cuerpo(asignacion, unidad, averaged=True)
    )
    familia = UserFactory(role=RoleFactory(name="Padre de familia", permissions={"notas": "ver"}))
    vincular_encargado_estudiante(
        guardian=GuardianFactory(user=familia), student=inscripcion.student, relationship="Madre"
    )

    para_familia = _cliente(familia).get(
        "/api/v1/grades/unit-summary/", {"enrollment": str(inscripcion.public_id)}
    )
    para_docente = _cliente(docente).get(
        "/api/v1/grades/unit-summary/", {"enrollment": str(inscripcion.public_id)}
    )

    assert para_familia.status_code == 200
    assert para_familia.data == [
        {"course_name": asignacion.course.name, "unit_number": 1, "nota": "70.00"}
    ]
    assert para_docente.data[0]["promediada"] is True


def test_rf29_una_familia_no_consulta_las_notas_de_otro_estudiante_acceso_no_autorizado():
    _, _, _, inscripcion = _unidad_incompleta()
    ajena = UserFactory(role=RoleFactory(name="Padre de familia", permissions={"notas": "ver"}))
    GuardianFactory(user=ajena)

    respuesta = _cliente(ajena).get(
        "/api/v1/grades/unit-summary/", {"enrollment": str(inscripcion.public_id)}
    )

    assert respuesta.status_code == 404
