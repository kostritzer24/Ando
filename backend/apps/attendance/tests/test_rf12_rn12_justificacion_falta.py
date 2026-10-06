import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.attendance.models import Attendance, Justification
from apps.catalog.models import JustificationType

from .factories import AttendanceFactory


@pytest.mark.django_db
def test_rf12_direccion_registra_una_justificacion():
    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    direccion = UserFactory(role=rol)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Constancia médica", requires_document=True)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/justifications/",
        {
            "attendance": str(asistencia.public_id),
            "justification_type": str(tipo.public_id),
            "reason_detail": "Consulta médica de emergencia.",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["resolution"] == Justification.RESOLUCION_PENDIENTE


@pytest.mark.django_db
def test_rn12_aprobar_la_justificacion_cambia_la_asistencia_a_justificado():
    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    direccion = UserFactory(role=rol)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Motivo familiar")

    client = APIClient()
    client.force_authenticate(user=direccion)

    creada = client.post(
        "/api/v1/justifications/",
        {"attendance": str(asistencia.public_id), "justification_type": str(tipo.public_id)},
        format="json",
    )
    justificacion_id = creada.data["public_id"]

    respuesta = client.post(
        f"/api/v1/justifications/{justificacion_id}/resolve/", {"aprobar": True}, format="json"
    )

    assert respuesta.status_code == 200
    assert respuesta.data["resolution"] == Justification.RESOLUCION_APROBADA
    asistencia.refresh_from_db()
    assert asistencia.status == Attendance.ESTADO_JUSTIFICADO


@pytest.mark.django_db
def test_rechazar_la_justificacion_no_cambia_la_asistencia():
    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    direccion = UserFactory(role=rol)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Motivo familiar")

    client = APIClient()
    client.force_authenticate(user=direccion)

    creada = client.post(
        "/api/v1/justifications/",
        {"attendance": str(asistencia.public_id), "justification_type": str(tipo.public_id)},
        format="json",
    )
    justificacion_id = creada.data["public_id"]

    respuesta = client.post(
        f"/api/v1/justifications/{justificacion_id}/resolve/", {"aprobar": False}, format="json"
    )

    assert respuesta.status_code == 200
    assert respuesta.data["resolution"] == Justification.RESOLUCION_RECHAZADA
    asistencia.refresh_from_db()
    assert asistencia.status == Attendance.ESTADO_AUSENTE


@pytest.mark.django_db
def test_rf12_seccion14_4_acepta_un_pdf_valido_como_documento_de_respaldo():
    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    direccion = UserFactory(role=rol)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Constancia médica", requires_document=True)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/justifications/",
        {
            "attendance": str(asistencia.public_id),
            "justification_type": str(tipo.public_id),
            "supporting_document": SimpleUploadedFile(
                "constancia.pdf", b"%PDF-1.4 contenido de prueba", content_type="application/pdf"
            ),
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.data["has_supporting_document"] is True


@pytest.mark.django_db
def test_rf12_seccion14_4_rechaza_una_extension_no_permitida():
    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    direccion = UserFactory(role=rol)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Constancia médica", requires_document=True)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/justifications/",
        {
            "attendance": str(asistencia.public_id),
            "justification_type": str(tipo.public_id),
            "supporting_document": SimpleUploadedFile(
                "script.exe", b"MZ contenido ejecutable", content_type="application/x-msdownload"
            ),
        },
    )

    assert respuesta.status_code == 400
    assert "supporting_document" in respuesta.data


@pytest.mark.django_db
def test_rf12_seccion14_4_rechaza_contenido_que_no_coincide_con_la_extension():
    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    direccion = UserFactory(role=rol)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Constancia médica", requires_document=True)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/justifications/",
        {
            "attendance": str(asistencia.public_id),
            "justification_type": str(tipo.public_id),
            "supporting_document": SimpleUploadedFile(
                "falso.pdf", b"esto no es un PDF de verdad", content_type="application/pdf"
            ),
        },
    )

    assert respuesta.status_code == 400
    assert "supporting_document" in respuesta.data


@pytest.mark.django_db
def test_rf12_seccion14_4_rechaza_un_archivo_demasiado_pesado():
    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    direccion = UserFactory(role=rol)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Constancia médica", requires_document=True)

    client = APIClient()
    client.force_authenticate(user=direccion)

    contenido_pesado = b"%PDF-1.4 " + b"0" * (5 * 1024 * 1024 + 1)
    respuesta = client.post(
        "/api/v1/justifications/",
        {
            "attendance": str(asistencia.public_id),
            "justification_type": str(tipo.public_id),
            "supporting_document": SimpleUploadedFile(
                "pesado.pdf", contenido_pesado, content_type="application/pdf"
            ),
        },
    )

    assert respuesta.status_code == 400
    assert "supporting_document" in respuesta.data


@pytest.mark.django_db
def test_solo_direccion_resuelve_justificaciones_acceso_no_autorizado():
    rol_guia = RoleFactory(name="Docente con sección a cargo", permissions={"asistencia": "editar"})
    guia = UserFactory(role=rol_guia)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Motivo familiar")

    client = APIClient()
    client.force_authenticate(user=guia)

    creada = client.post(
        "/api/v1/justifications/",
        {"attendance": str(asistencia.public_id), "justification_type": str(tipo.public_id)},
        format="json",
    )
    assert creada.status_code == 201
    justificacion_id = creada.data["public_id"]

    respuesta = client.post(
        f"/api/v1/justifications/{justificacion_id}/resolve/", {"aprobar": True}, format="json"
    )

    assert respuesta.status_code == 403
    asistencia.refresh_from_db()
    assert asistencia.status == Attendance.ESTADO_AUSENTE


@pytest.mark.django_db
def test_rnf06_aprobar_una_justificacion_deja_el_cambio_de_estado_en_bitacora():
    from apps.core.models import AuditLog

    rol = RoleFactory(name="Dirección", permissions={"asistencia": "editar"})
    direccion = UserFactory(role=rol)
    asistencia = AttendanceFactory(status=Attendance.ESTADO_AUSENTE)
    tipo = JustificationType.objects.create(name="Cita médica")
    client = APIClient()
    client.force_authenticate(user=direccion)
    creada = client.post(
        "/api/v1/justifications/",
        {"attendance": str(asistencia.public_id), "justification_type": str(tipo.public_id)},
        format="json",
    )

    client.post(
        f"/api/v1/justifications/{creada.data['public_id']}/resolve/",
        {"aprobar": True},
        format="json",
    )

    cambio = AuditLog.objects.get(entity_name="attendance.Attendance", action="actualizar")
    assert cambio.old_value == {"status": Attendance.ESTADO_AUSENTE}
    assert cambio.new_value == {"status": Attendance.ESTADO_JUSTIFICADO}
