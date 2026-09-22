import io

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import load_workbook
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import GradingUnitFactory
from apps.grading.models import Grade, GradeChangeRequest
from apps.students.tests.factories import EnrollmentFactory, StudentFactory

from .factories import ActivityFactory, ActivityTypeFactory, TeacherAssignmentFactory


def _docente_con_actividades_y_estudiantes(cantidad=2):
    rol = RoleFactory(name="Docente", permissions={"notas": "editar"})
    docente = UserFactory(role=rol)
    asignacion = TeacherAssignmentFactory(teacher=docente)
    unidad = GradingUnitFactory(cycle=asignacion.cycle)
    tipo = ActivityTypeFactory(name="Prueba corta")
    actividad = ActivityFactory(
        assignment=asignacion, unit=unidad, activity_type=tipo, name="Prueba corta 1", max_score=10
    )
    inscripciones = []
    for indice in range(cantidad):
        estudiante = StudentFactory(internal_code=f"ES{indice + 1:03d}")
        inscripciones.append(
            EnrollmentFactory(
                student=estudiante, section=asignacion.section, cycle=asignacion.cycle
            )
        )
    return docente, asignacion, unidad, actividad, inscripciones


def _archivo_xlsx(filas: list[tuple]) -> SimpleUploadedFile:
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.append(["Código", "Nombre", "Prueba corta 1 (máx 10)"])
    for fila in filas:
        hoja.append(list(fila))
    buffer = io.BytesIO()
    libro.save(buffer)
    buffer.seek(0)
    return SimpleUploadedFile(
        "notas.xlsx",
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@pytest.mark.django_db
def test_rf19_generar_plantilla_incluye_actividad_y_estudiantes():
    docente, asignacion, unidad, _actividad, _inscripciones = (
        _docente_con_actividades_y_estudiantes(2)
    )

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get(f"/api/v1/grades/template/{asignacion.public_id}/{unidad.public_id}/")

    assert respuesta.status_code == 200
    libro = load_workbook(io.BytesIO(respuesta.content))
    hoja = libro.active
    encabezados = [c.value for c in next(hoja.iter_rows(max_row=1))]
    assert "Prueba corta 1" in encabezados[2]
    codigos = [fila[0].value for fila in hoja.iter_rows(min_row=2)]
    assert codigos == ["ES001", "ES002"]


@pytest.mark.django_db
def test_rf20_preview_clasifica_las_celdas_sin_guardar_nada():
    docente, asignacion, unidad, _actividad, _inscripciones = (
        _docente_con_actividades_y_estudiantes(1)
    )
    archivo = _archivo_xlsx([("ES001", "Estudiante Uno", "8")])

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grades/template/preview/",
        {"assignment": str(asignacion.public_id), "unit": str(unidad.public_id), "file": archivo},
        format="multipart",
    )

    assert respuesta.status_code == 200
    assert respuesta.data["resumen"]["crear"] == 1
    assert not Grade.objects.exists()


@pytest.mark.django_db
def test_rf20_cargar_plantilla_valida_crea_las_notas():
    docente, asignacion, unidad, actividad, inscripciones = _docente_con_actividades_y_estudiantes(
        2
    )
    archivo = _archivo_xlsx([("ES001", "Estudiante Uno", "8"), ("ES002", "Estudiante Dos", "10")])

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grades/template/upload/",
        {"assignment": str(asignacion.public_id), "unit": str(unidad.public_id), "file": archivo},
        format="multipart",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["creados"] == 2
    assert Grade.objects.filter(activity=actividad, source="plantilla").count() == 2


@pytest.mark.django_db
def test_rn07_recargar_la_plantilla_con_otra_nota_crea_una_solicitud_de_modificacion():
    docente, asignacion, unidad, actividad, inscripciones = _docente_con_actividades_y_estudiantes(
        1
    )
    Grade.objects.create(
        enrollment=inscripciones[0],
        activity=actividad,
        raw_score=7,
        current_score=7,
        recorded_by=docente,
    )
    archivo = _archivo_xlsx([("ES001", "Estudiante Uno", "9")])

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grades/template/upload/",
        {"assignment": str(asignacion.public_id), "unit": str(unidad.public_id), "file": archivo},
        format="multipart",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["solicitudes_de_modificacion"] == 1
    assert respuesta.data["creados"] == 0

    calificacion = Grade.objects.get(activity=actividad, enrollment=inscripciones[0])
    assert calificacion.current_score == 7  # sin cambios hasta que Dirección apruebe
    assert calificacion.raw_score == 7
    assert GradeChangeRequest.objects.filter(grade=calificacion, requested_score=9).exists()


@pytest.mark.django_db
def test_rn07_recargar_con_la_misma_nota_no_genera_nada():
    docente, asignacion, unidad, actividad, inscripciones = _docente_con_actividades_y_estudiantes(
        1
    )
    Grade.objects.create(
        enrollment=inscripciones[0],
        activity=actividad,
        raw_score=7,
        current_score=7,
        recorded_by=docente,
    )
    archivo = _archivo_xlsx([("ES001", "Estudiante Uno", "7")])

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grades/template/upload/",
        {"assignment": str(asignacion.public_id), "unit": str(unidad.public_id), "file": archivo},
        format="multipart",
    )

    assert respuesta.status_code == 201
    assert respuesta.data == {"creados": 0, "solicitudes_de_modificacion": 0}
    assert GradeChangeRequest.objects.count() == 0


@pytest.mark.django_db
def test_rf20_codigo_ajeno_no_guarda_nada():
    docente, asignacion, unidad, _actividad, _inscripciones = (
        _docente_con_actividades_y_estudiantes(1)
    )
    archivo = _archivo_xlsx([("ES999", "No pertenece", "8")])

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grades/template/upload/",
        {"assignment": str(asignacion.public_id), "unit": str(unidad.public_id), "file": archivo},
        format="multipart",
    )

    assert respuesta.status_code == 400
    assert not Grade.objects.exists()


@pytest.mark.django_db
def test_rechaza_archivos_que_no_son_xlsx():
    docente, asignacion, unidad, _actividad, _inscripciones = (
        _docente_con_actividades_y_estudiantes(1)
    )
    archivo_falso = SimpleUploadedFile(
        "notas.xlsm", b"contenido", content_type="application/octet-stream"
    )

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grades/template/upload/",
        {
            "assignment": str(asignacion.public_id),
            "unit": str(unidad.public_id),
            "file": archivo_falso,
        },
        format="multipart",
    )

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_docente_no_puede_cargar_plantilla_de_una_asignacion_ajena_acceso_no_autorizado():
    rol = RoleFactory(name="Docente", permissions={"notas": "editar"})
    docente = UserFactory(role=rol)
    _otro, asignacion_ajena, unidad, _actividad, _inscripciones = (
        _docente_con_actividades_y_estudiantes(1)
    )
    archivo = _archivo_xlsx([("ES001", "Estudiante Uno", "8")])

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/grades/template/upload/",
        {
            "assignment": str(asignacion_ajena.public_id),
            "unit": str(unidad.public_id),
            "file": archivo,
        },
        format="multipart",
    )

    assert respuesta.status_code == 403
