import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import SectionFactory
from apps.communication.models import Conversation, Message
from apps.scheduling.tests.factories import TeacherAssignmentFactory
from apps.students.models import Enrollment
from apps.students.services.link import vincular_encargado_estudiante
from apps.students.tests.factories import EnrollmentFactory, GuardianFactory, StudentFactory

pytestmark = pytest.mark.django_db

URL = "/api/v1/conversations/"


def _familia_con_hijo(seccion, *, encargado="Ana López", hijo="Luis"):
    rol = RoleFactory(name="Padre de familia", permissions={"buzon": "editar"})
    usuario = UserFactory(role=rol)
    guardian = GuardianFactory(user=usuario, full_name=encargado)
    estudiante = StudentFactory(first_name=hijo, last_name="Pérez")
    vincular_encargado_estudiante(guardian=guardian, student=estudiante, relationship="Madre")
    EnrollmentFactory(student=estudiante, section=seccion, cycle=seccion.cycle)
    return usuario


def _hijo_de(familia):
    return familia.guardian.student_links.get().student


def _docente():
    return UserFactory(role=RoleFactory(name="Docente", permissions={"buzon": "editar"}))


def _guia_de(seccion):
    guia = _docente()
    seccion.homeroom_teacher = guia
    seccion.save(update_fields=["homeroom_teacher"])
    return guia


def _direccion():
    return UserFactory(role=RoleFactory(name="Dirección", permissions={"buzon": "editar"}))


def _cliente(usuario):
    client = APIClient()
    client.force_authenticate(user=usuario)
    return client


def _familia_escribe(familia, *, subject="Consulta", content="¿Hay tarea para mañana?"):
    return _cliente(familia).post(
        URL, {"student": str(_hijo_de(familia).public_id), "subject": subject, "content": content}
    )


def _escribir_a(remitente, familia, *, subject="Aviso", content="Buenos días."):
    return _cliente(remitente).post(
        URL,
        {
            "guardian": str(familia.guardian.public_id),
            "student": str(_hijo_de(familia).public_id),
            "subject": subject,
            "content": content,
        },
    )


def test_rf37_la_familia_inicia_una_conversacion_hacia_la_seccion_de_su_hijo():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    familia = _familia_con_hijo(seccion)

    envio = _familia_escribe(familia)

    assert envio.status_code == 201
    conversacion = Conversation.objects.get()
    assert conversacion.section == seccion
    assert conversacion.created_by == familia
    assert envio.data["messages"][0]["sender_label"] == "Ana López / Luis Pérez"
    bandeja = _cliente(guia).get(URL)
    assert bandeja.data["count"] == 1
    assert bandeja.data["results"][0]["no_leido"] is True


def test_rf25_rf37_todos_los_participantes_responden_incluida_la_familia():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    familia = _familia_con_hijo(seccion)
    conversacion_id = _familia_escribe(familia).data["public_id"]

    del_guia = _cliente(guia).post(f"{URL}{conversacion_id}/reply/", {"content": "Sí, matemática."})
    de_la_familia = _cliente(familia).post(f"{URL}{conversacion_id}/reply/", {"content": "Gracias"})

    assert del_guia.status_code == 201
    assert del_guia.data["sender_role"] == "Docente"
    assert del_guia.data["sender_name"] == guia.nombre_completo()
    assert de_la_familia.status_code == 201
    detalle = _cliente(guia).get(f"{URL}{conversacion_id}/")
    assert [m["content"] for m in detalle.data["messages"]] == [
        "¿Hay tarea para mañana?",
        "Sí, matemática.",
        "Gracias",
    ]


def test_rf38_un_docente_inicia_una_conversacion_con_un_encargado_de_otra_seccion():
    seccion = SectionFactory()
    familia = _familia_con_hijo(seccion)
    docente = _docente()  # no da clase en la sección

    envio = _escribir_a(docente, familia)

    assert envio.status_code == 201
    # La ve porque la inició, aunque no dé clase en esa sección.
    assert _cliente(docente).get(URL).data["count"] == 1
    bandeja_familia = _cliente(familia).get(URL)
    assert bandeja_familia.data["count"] == 1
    assert bandeja_familia.data["results"][0]["no_leido"] is True


def test_rf38_direccion_inicia_una_conversacion_con_un_encargado():
    familia = _familia_con_hijo(SectionFactory())

    envio = _escribir_a(_direccion(), familia)

    assert envio.status_code == 201
    assert envio.data["created_by_name"]


def test_rf38_el_centro_debe_elegir_el_encargado():
    familia = _familia_con_hijo(SectionFactory())

    respuesta = _cliente(_docente()).post(
        URL, {"student": str(_hijo_de(familia).public_id), "subject": "Hola", "content": "..."}
    )

    assert respuesta.status_code == 400


def test_rf38_no_se_inicia_con_un_encargado_que_no_es_de_ese_estudiante():
    seccion = SectionFactory()
    familia = _familia_con_hijo(seccion)
    otra = _familia_con_hijo(seccion, encargado="Rosa Gil", hijo="Pedro")

    respuesta = _cliente(_direccion()).post(
        URL,
        {
            "guardian": str(familia.guardian.public_id),
            "student": str(_hijo_de(otra).public_id),
            "subject": "Hola",
            "content": "...",
        },
    )

    assert respuesta.status_code == 400
    assert Conversation.objects.count() == 0


def test_rn19_una_familia_no_ve_ni_responde_la_conversacion_de_otra_acceso_no_autorizado():
    seccion = SectionFactory()
    _guia_de(seccion)
    familia_a = _familia_con_hijo(seccion)
    familia_b = _familia_con_hijo(seccion, encargado="Rosa Gil", hijo="Pedro")
    conversacion_id = _familia_escribe(familia_a).data["public_id"]

    client_b = _cliente(familia_b)

    assert client_b.get(URL).data["count"] == 0
    assert client_b.get(f"{URL}{conversacion_id}/").status_code == 404
    assert client_b.post(f"{URL}{conversacion_id}/reply/", {"content": "..."}).status_code == 404
    assert Message.objects.count() == 1


def test_rf37_la_familia_no_inicia_sobre_un_estudiante_ajeno():
    seccion = SectionFactory()
    familia = _familia_con_hijo(seccion)
    otra = _familia_con_hijo(seccion, encargado="Rosa Gil", hijo="Pedro")

    respuesta = _cliente(familia).post(
        URL, {"student": str(_hijo_de(otra).public_id), "subject": "Intento", "content": "..."}
    )

    assert respuesta.status_code == 403


def test_rn19_un_docente_ajeno_a_la_seccion_no_ve_la_conversacion():
    seccion = SectionFactory()
    familia = _familia_con_hijo(seccion)
    _familia_escribe(familia)
    ajeno = _docente()

    client = _cliente(ajeno)

    assert client.get(URL).data["count"] == 0
    conversacion_id = Conversation.objects.get().public_id
    assert client.post(f"{URL}{conversacion_id}/reply/", {"content": "..."}).status_code == 404


def test_rn19_un_docente_asignado_a_la_seccion_ve_la_conversacion():
    seccion = SectionFactory()
    familia = _familia_con_hijo(seccion)
    docente = _docente()
    TeacherAssignmentFactory(teacher=docente, section=seccion, cycle=seccion.cycle)
    _escribir_a(_direccion(), familia)

    assert _cliente(docente).get(URL).data["count"] == 1


def test_rn19_el_no_leido_es_de_cada_persona():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    familia = _familia_con_hijo(seccion)
    direccion = _direccion()
    conversacion_id = _familia_escribe(familia).data["public_id"]

    # Quien escribe no tiene su propio mensaje como pendiente.
    assert _cliente(familia).get(URL).data["results"][0]["no_leido"] is False
    _cliente(guia).get(f"{URL}{conversacion_id}/")  # el guía la abre

    assert _cliente(guia).get(URL).data["results"][0]["no_leido"] is False
    # Que la abriera el guía no la marca para Dirección.
    assert _cliente(direccion).get(URL).data["results"][0]["no_leido"] is True

    _cliente(guia).post(f"{URL}{conversacion_id}/reply/", {"content": "Respondo."})
    assert _cliente(familia).get(URL).data["results"][0]["no_leido"] is True


def test_rn19_el_contador_del_menu_cuenta_solo_lo_no_leido_de_quien_consulta():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    familia_a = _familia_con_hijo(seccion)
    familia_b = _familia_con_hijo(seccion, encargado="Rosa Gil", hijo="Pedro")
    primera = _familia_escribe(familia_a).data["public_id"]
    _familia_escribe(familia_b)

    client = _cliente(guia)
    assert client.get(f"{URL}unread-count/").data == {"no_leidas": 2}
    client.get(f"{URL}{primera}/")
    assert client.get(f"{URL}unread-count/").data == {"no_leidas": 1}
    assert _cliente(familia_a).get(f"{URL}unread-count/").data == {"no_leidas": 0}


def test_rn19_la_bandeja_va_del_ultimo_mensaje_al_primero():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    familia_a = _familia_con_hijo(seccion)
    familia_b = _familia_con_hijo(seccion, encargado="Rosa Gil", hijo="Pedro")
    vieja = _familia_escribe(familia_a, subject="Vieja").data["public_id"]
    _familia_escribe(familia_b, subject="Nueva")

    _cliente(guia).post(f"{URL}{vieja}/reply/", {"content": "La reactivo."})

    asuntos = [c["subject"] for c in _cliente(guia).get(URL).data["results"]]
    assert asuntos == ["Vieja", "Nueva"]


def test_rf38_el_buscador_muestra_encargado_y_alumno_y_busca_por_cualquiera():
    seccion = SectionFactory()
    _familia_con_hijo(seccion, encargado="Ana López", hijo="Luis")
    otra = _familia_con_hijo(seccion, encargado="Rosa Gil", hijo="Pedro")
    retirado = otra.guardian.student_links.get().student.enrollments.get()
    client = _cliente(_docente())

    por_encargado = client.get(f"{URL}recipients/", {"q": "ana"}).data
    por_alumno = client.get(f"{URL}recipients/", {"q": "luis"}).data
    retirado.status = Enrollment.ESTADO_RETIRADO
    retirado.save(update_fields=["status"])
    todos = client.get(f"{URL}recipients/").data

    assert [r["label"] for r in por_encargado] == ["Ana López / Luis Pérez"]
    assert por_alumno == por_encargado
    # Solo encargados de estudiantes con inscripción activa.
    assert [r["label"] for r in todos] == ["Ana López / Luis Pérez"]


def test_rf38_la_familia_no_usa_el_buscador_acceso_no_autorizado():
    familia = _familia_con_hijo(SectionFactory())

    assert _cliente(familia).get(f"{URL}recipients/").status_code == 403


def test_rn16_un_mensaje_con_lenguaje_inapropiado_se_rechaza_y_bloquea_la_cuenta():
    familia = _familia_con_hijo(SectionFactory())

    respuesta = _familia_escribe(familia, content="El maestro es un idiota")

    assert respuesta.status_code == 400
    familia.refresh_from_db()
    assert familia.esta_bloqueado is True
    assert familia.locked_until > timezone.now()
    assert Conversation.objects.count() == 0
    assert Message.objects.count() == 0


def test_rn16_el_asunto_tambien_pasa_por_el_filtro():
    familia = _familia_con_hijo(SectionFactory())

    respuesta = _familia_escribe(familia, subject="Pendejo", content="Hola")

    assert respuesta.status_code == 400
    assert Conversation.objects.count() == 0


def test_rn16_una_respuesta_inapropiada_bloquea_a_quien_responde_sea_del_centro_o_familia():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    familia = _familia_con_hijo(seccion)
    conversacion_id = _escribir_a(guia, familia).data["public_id"]

    de_la_familia = _cliente(familia).post(f"{URL}{conversacion_id}/reply/", {"content": "put0"})
    del_guia = _cliente(guia).post(f"{URL}{conversacion_id}/reply/", {"content": "Qué idiota"})

    assert de_la_familia.status_code == 400
    assert del_guia.status_code == 400
    familia.refresh_from_db()
    guia.refresh_from_db()
    assert familia.esta_bloqueado and guia.esta_bloqueado
    assert Message.objects.count() == 1


def test_rn16_un_docente_que_inicia_con_lenguaje_inapropiado_queda_bloqueado():
    familia = _familia_con_hijo(SectionFactory())
    docente = _docente()

    respuesta = _escribir_a(docente, familia, content="Su hijo es un imbecil")

    assert respuesta.status_code == 400
    docente.refresh_from_db()
    assert docente.esta_bloqueado is True


def test_rn16_con_la_cuenta_bloqueada_no_se_puede_seguir_enviando_mensajes():
    """Hallazgo D-001: el bloqueo solo se revisaba al iniciar sesión, y el
    token emitido antes seguía enviando."""
    familia = _familia_con_hijo(SectionFactory())
    _familia_escribe(familia, content="eres un idiota")
    familia.refresh_from_db()
    assert familia.esta_bloqueado is True

    segundo = _familia_escribe(familia, content="Buenos días")

    assert segundo.status_code == 400
    assert Message.objects.filter(sender=familia).count() == 0


def test_rf25_un_rol_sin_buzon_no_entra_acceso_no_autorizado():
    tallerista = UserFactory(
        role=RoleFactory(name="Tallerista", permissions={"buzon": "sin_acceso"})
    )

    assert _cliente(tallerista).get(URL).status_code == 403
