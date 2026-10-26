from datetime import date, datetime, timedelta, timezone

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

pytestmark = pytest.mark.django_db(transaction=True)

ANTES = [("communication", "0003_reporte_conducta_borrador_publicado")]
DESPUES = [("communication", "0006_mensaje_dentro_de_conversacion")]


def _migrar(destino):
    executor = MigrationExecutor(connection)
    executor.loader.build_graph()
    executor.migrate(destino)
    return executor.loader.project_state(destino).apps


def test_rf25_rn19_cada_hilo_viejo_pasa_a_ser_una_conversacion_con_sus_fechas_y_lecturas():
    apps = _migrar(ANTES)
    Role = apps.get_model("accounts", "Role")
    User = apps.get_model("accounts", "User")
    SchoolCycle = apps.get_model("catalog", "SchoolCycle")
    Section = apps.get_model("catalog", "Section")
    Student = apps.get_model("students", "Student")
    Guardian = apps.get_model("students", "Guardian")
    GuardianStudentLink = apps.get_model("students", "GuardianStudentLink")
    Enrollment = apps.get_model("students", "Enrollment")
    Message = apps.get_model("communication", "Message")

    rol_familia = Role.objects.create(name="Padre de familia", permissions={})
    rol_docente = Role.objects.create(name="Docente", permissions={})
    familia = User.objects.create(username="familia.m", role=rol_familia)
    docente = User.objects.create(username="docente.m", role=rol_docente)
    otro_docente = User.objects.create(username="docente.n", role=rol_docente)
    ciclo = SchoolCycle.objects.create(
        year=2026, start_date=date(2026, 1, 12), end_date=date(2026, 10, 30)
    )
    seccion = Section.objects.create(cycle=ciclo, grade="Primero", letter="A", type="academica")
    hijo = Student.objects.create(
        internal_code="ES900", first_name="Luis", last_name="Pérez", birth_date=date(2013, 5, 1)
    )
    guardian = Guardian.objects.create(user=familia, full_name="Ana López")
    GuardianStudentLink.objects.create(guardian=guardian, student=hijo, relationship="Madre")
    Enrollment.objects.create(
        student=hijo, section=seccion, cycle=ciclo, enrolled_at=date(2026, 1, 12)
    )

    base = datetime(2026, 3, 1, 8, tzinfo=timezone.utc)
    raiz = Message.objects.create(
        sender=familia, section=seccion, subject="Tarea", content="¿Hay tarea?", status="respondido"
    )
    respuesta = Message.objects.create(
        sender=docente, section=seccion, content="Sí.", original_message=raiz
    )
    solo_leido = Message.objects.create(
        sender=familia, section=seccion, subject="Otra", content="Hola", status="leido"
    )
    for mensaje, horas in ((raiz, 0), (respuesta, 2), (solo_leido, 5)):
        Message.objects.filter(id=mensaje.id).update(created_at=base + timedelta(hours=horas))

    apps = _migrar(DESPUES)
    Conversation = apps.get_model("communication", "Conversation")
    ConversationRead = apps.get_model("communication", "ConversationRead")
    Message = apps.get_model("communication", "Message")

    tarea = Conversation.objects.get(subject="Tarea")
    assert tarea.student_id == hijo.id
    assert tarea.guardian_id == guardian.id
    assert tarea.section_id == seccion.id
    assert tarea.created_by_id == familia.id
    assert tarea.created_at == base
    assert tarea.last_message_at == base + timedelta(hours=2)
    mensajes = Message.objects.filter(conversation=tarea).order_by("created_at")
    assert [(m.public_id, m.sender_id) for m in mensajes] == [
        (raiz.public_id, familia.id),
        (respuesta.public_id, docente.id),
    ]
    lecturas = dict(
        ConversationRead.objects.filter(conversation=tarea).values_list("user_id", "last_read_at")
    )
    # La familia leyó hasta su mensaje (la respuesta le queda pendiente) y
    # el docente hasta su respuesta.
    assert lecturas == {familia.id: base, docente.id: base + timedelta(hours=2)}

    otra = Conversation.objects.get(subject="Otra")
    # "Leído" sin respuesta no dice quién lo leyó: no se inventa una lectura.
    assert set(
        ConversationRead.objects.filter(conversation=otra).values_list("user_id", flat=True)
    ) == {familia.id}
    assert not ConversationRead.objects.filter(user_id=otro_docente.id).exists()
