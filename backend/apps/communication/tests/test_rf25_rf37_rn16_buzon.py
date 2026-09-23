import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import SectionFactory
from apps.students.services.link import vincular_encargado_estudiante
from apps.students.tests.factories import EnrollmentFactory, GuardianFactory, StudentFactory

pytestmark = pytest.mark.django_db


def _familia_con_hijo(seccion):
    rol = RoleFactory(name="Padre de familia", permissions={"buzon": "editar"})
    usuario = UserFactory(role=rol)
    encargado = GuardianFactory(user=usuario)
    hijo = StudentFactory()
    vincular_encargado_estudiante(guardian=encargado, student=hijo, relationship="Madre")
    EnrollmentFactory(student=hijo, section=seccion, cycle=seccion.cycle)
    return usuario


def _guia_de(seccion):
    rol = RoleFactory(name="Docente con sección a cargo", permissions={"buzon": "editar"})
    guia = UserFactory(role=rol)
    seccion.homeroom_teacher = guia
    seccion.save(update_fields=["homeroom_teacher"])
    return guia


def _direccion():
    rol = RoleFactory(name="Dirección", permissions={"buzon": "editar"})
    return UserFactory(role=rol)


def test_rf25_rf37_la_familia_envia_un_mensaje_y_el_guia_lo_ve_y_responde():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    familia = _familia_con_hijo(seccion)

    client_familia = APIClient()
    client_familia.force_authenticate(user=familia)
    envio = client_familia.post(
        "/api/v1/messages/",
        {
            "section": str(seccion.public_id),
            "subject": "Consulta",
            "content": "¿Hay tarea para mañana?",
        },
    )
    assert envio.status_code == 201
    assert envio.data["status"] == "enviado"

    client_guia = APIClient()
    client_guia.force_authenticate(user=guia)
    bandeja = client_guia.get("/api/v1/messages/")
    assert bandeja.data["count"] == 1
    hilo_id = bandeja.data["results"][0]["public_id"]

    respuesta = client_guia.post(
        f"/api/v1/messages/{hilo_id}/reply/", {"content": "Sí, matemática."}
    )
    assert respuesta.status_code == 201

    hilo = client_guia.get(f"/api/v1/messages/{hilo_id}/")
    assert hilo.data["status"] == "respondido"


def test_rf25_la_familia_no_ve_hilos_de_otras_familias():
    seccion = SectionFactory()
    _guia_de(seccion)
    familia_a = _familia_con_hijo(seccion)
    familia_b = _familia_con_hijo(seccion)

    client_a = APIClient()
    client_a.force_authenticate(user=familia_a)
    client_a.post(
        "/api/v1/messages/",
        {"section": str(seccion.public_id), "subject": "A", "content": "Mensaje de A"},
    )

    client_b = APIClient()
    client_b.force_authenticate(user=familia_b)
    bandeja_b = client_b.get("/api/v1/messages/")

    assert bandeja_b.data["count"] == 0


def test_rf37_la_familia_no_puede_enviar_a_una_seccion_ajena():
    seccion_propia = SectionFactory()
    seccion_ajena = SectionFactory()
    _guia_de(seccion_ajena)
    familia = _familia_con_hijo(seccion_propia)

    client = APIClient()
    client.force_authenticate(user=familia)
    respuesta = client.post(
        "/api/v1/messages/",
        {"section": str(seccion_ajena.public_id), "subject": "Intento", "content": "..."},
    )

    assert respuesta.status_code == 403


def test_rf25_la_familia_no_puede_responder_un_hilo():
    seccion = SectionFactory()
    _guia_de(seccion)
    familia = _familia_con_hijo(seccion)

    client = APIClient()
    client.force_authenticate(user=familia)
    envio = client.post(
        "/api/v1/messages/",
        {"section": str(seccion.public_id), "subject": "Consulta", "content": "..."},
    )
    hilo_id = envio.data["public_id"]

    respuesta = client.post(f"/api/v1/messages/{hilo_id}/reply/", {"content": "..."})

    assert respuesta.status_code == 403


def test_rn16_un_mensaje_con_lenguaje_inapropiado_se_rechaza_y_bloquea_la_cuenta():
    seccion = SectionFactory()
    _guia_de(seccion)
    familia = _familia_con_hijo(seccion)
    assert familia.esta_bloqueado is False

    client = APIClient()
    client.force_authenticate(user=familia)
    respuesta = client.post(
        "/api/v1/messages/",
        {
            "section": str(seccion.public_id),
            "subject": "Queja",
            "content": "El maestro es un idiota",
        },
    )

    assert respuesta.status_code == 400
    familia.refresh_from_db()
    assert familia.esta_bloqueado is True
    assert familia.locked_until > timezone.now()


def test_rn16_no_se_crea_ningun_mensaje_cuando_el_filtro_lo_rechaza():
    from apps.communication.models import Message

    seccion = SectionFactory()
    _guia_de(seccion)
    familia = _familia_con_hijo(seccion)

    client = APIClient()
    client.force_authenticate(user=familia)
    client.post(
        "/api/v1/messages/",
        {"section": str(seccion.public_id), "subject": "Queja", "content": "Sos un pendejo"},
    )

    assert Message.objects.count() == 0


def test_rn16_una_respuesta_con_lenguaje_inapropiado_tambien_bloquea_a_quien_responde():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    familia = _familia_con_hijo(seccion)

    client_familia = APIClient()
    client_familia.force_authenticate(user=familia)
    envio = client_familia.post(
        "/api/v1/messages/",
        {"section": str(seccion.public_id), "subject": "Consulta", "content": "..."},
    )

    client_guia = APIClient()
    client_guia.force_authenticate(user=guia)
    respuesta = client_guia.post(
        f"/api/v1/messages/{envio.data['public_id']}/reply/", {"content": "Qué pregunta de idiota"}
    )

    assert respuesta.status_code == 400
    guia.refresh_from_db()
    assert guia.esta_bloqueado is True


def test_rf25_al_consultar_el_hilo_el_guia_lo_marca_como_leido():
    seccion = SectionFactory()
    guia = _guia_de(seccion)
    familia = _familia_con_hijo(seccion)

    client_familia = APIClient()
    client_familia.force_authenticate(user=familia)
    envio = client_familia.post(
        "/api/v1/messages/",
        {"section": str(seccion.public_id), "subject": "Consulta", "content": "..."},
    )

    client_guia = APIClient()
    client_guia.force_authenticate(user=guia)
    detalle = client_guia.get(f"/api/v1/messages/{envio.data['public_id']}/")

    assert detalle.data["status"] == "leido"


def test_rf25_direccion_ve_y_responde_cualquier_hilo():
    seccion = SectionFactory()
    _guia_de(seccion)
    familia = _familia_con_hijo(seccion)
    dir_user = _direccion()

    client_familia = APIClient()
    client_familia.force_authenticate(user=familia)
    envio = client_familia.post(
        "/api/v1/messages/",
        {"section": str(seccion.public_id), "subject": "Consulta", "content": "..."},
    )

    client_dir = APIClient()
    client_dir.force_authenticate(user=dir_user)
    respuesta = client_dir.post(
        f"/api/v1/messages/{envio.data['public_id']}/reply/", {"content": "Ya lo reviso."}
    )

    assert respuesta.status_code == 201
