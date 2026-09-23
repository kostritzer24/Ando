from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import SectionFactory
from apps.communication.models import Announcement

pytestmark = pytest.mark.django_db


def _direccion():
    rol = RoleFactory(name="Dirección", permissions={"avisos": "editar"})
    return UserFactory(role=rol)


def test_rf13_direccion_publica_un_aviso_para_todos():
    client = APIClient()
    client.force_authenticate(user=_direccion())

    respuesta = client.post(
        "/api/v1/announcements/",
        {"title": "Suspensión de labores", "content": "Por lluvia.", "audience": "todos"},
    )

    assert respuesta.status_code == 201
    assert respuesta.data["audience"] == "todos"


def test_rf13_aviso_para_seccion_sin_elegir_cual_se_rechaza():
    client = APIClient()
    client.force_authenticate(user=_direccion())

    respuesta = client.post(
        "/api/v1/announcements/",
        {"title": "Reunión", "content": "Solo esta sección.", "audience": "seccion"},
    )

    assert respuesta.status_code == 400


def test_rf13_docente_no_puede_publicar_acceso_no_autorizado():
    rol = RoleFactory(name="Docente", permissions={"avisos": "ver"})
    docente = UserFactory(role=rol)
    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/announcements/", {"title": "Intento", "content": "...", "audience": "todos"}
    )

    assert respuesta.status_code == 403


def test_hu36_los_avisos_vencidos_dejan_de_mostrarse():
    Announcement.objects.create(
        title="Vigente", content="...", audience="todos", published_by=_direccion()
    )
    Announcement.objects.create(
        title="Vencido",
        content="...",
        audience="todos",
        published_by=_direccion(),
        expires_at=timezone.now() - timedelta(days=1),
    )
    rol = RoleFactory(name="Docente", permissions={"avisos": "ver"})
    docente = UserFactory(role=rol)
    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get("/api/v1/announcements/")

    titulos = {a["title"] for a in respuesta.data["results"]}
    assert titulos == {"Vigente"}


def test_hu36_direccion_ve_tambien_los_vencidos_para_administrarlos():
    dir_user = _direccion()
    Announcement.objects.create(
        title="Vencido",
        content="...",
        audience="todos",
        published_by=dir_user,
        expires_at=timezone.now() - timedelta(days=1),
    )
    client = APIClient()
    client.force_authenticate(user=dir_user)

    respuesta = client.get("/api/v1/announcements/")

    assert respuesta.data["count"] == 1


def test_rf13_aviso_de_seccion_solo_lo_ve_quien_esta_conectado_a_esa_seccion():
    dir_user = _direccion()
    seccion_a = SectionFactory()
    seccion_b = SectionFactory()
    Announcement.objects.create(
        title="Solo sección A",
        content="...",
        audience="seccion",
        target_section=seccion_a,
        published_by=dir_user,
    )

    rol_guia = RoleFactory(name="Docente con sección a cargo", permissions={"avisos": "ver"})
    guia_de_a = UserFactory(role=rol_guia)
    seccion_a.homeroom_teacher = guia_de_a
    seccion_a.save(update_fields=["homeroom_teacher"])

    from apps.scheduling.tests.factories import TeacherAssignmentFactory

    TeacherAssignmentFactory(teacher=guia_de_a, section=seccion_a, cycle=seccion_a.cycle)
    guia_de_b = UserFactory(role=rol_guia)
    TeacherAssignmentFactory(teacher=guia_de_b, section=seccion_b, cycle=seccion_b.cycle)

    client_a = APIClient()
    client_a.force_authenticate(user=guia_de_a)
    assert client_a.get("/api/v1/announcements/").data["count"] == 1

    client_b = APIClient()
    client_b.force_authenticate(user=guia_de_b)
    assert client_b.get("/api/v1/announcements/").data["count"] == 0
