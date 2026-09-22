import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import Section

from .factories import SchoolCycleFactory, SectionFactory


@pytest.mark.django_db
def test_seccion_taller_con_maestro_guia_es_rechazada_por_la_api():
    rol_direccion = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar"})
    direccion = UserFactory(role=rol_direccion)
    rol_guia = RoleFactory(name="Docente con sección a cargo")
    maestro = UserFactory(role=rol_guia)
    ciclo = SchoolCycleFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/sections/",
        {
            "cycle": str(ciclo.public_id),
            "grade": "Taller de panadería",
            "type": Section.TIPO_TALLER,
            "homeroom_teacher": str(maestro.public_id),
        },
        format="json",
    )

    assert respuesta.status_code == 400
    assert not Section.objects.filter(grade="Taller de panadería").exists()


@pytest.mark.django_db
def test_seccion_academica_con_maestro_guia_se_crea_correctamente():
    rol_direccion = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar"})
    direccion = UserFactory(role=rol_direccion)
    rol_guia = RoleFactory(name="Docente con sección a cargo")
    maestro = UserFactory(role=rol_guia)
    ciclo = SchoolCycleFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/sections/",
        {
            "cycle": str(ciclo.public_id),
            "grade": "Segundo básico",
            "letter": "A",
            "type": Section.TIPO_ACADEMICA,
            "homeroom_teacher": str(maestro.public_id),
        },
        format="json",
    )

    assert respuesta.status_code == 201
    seccion = Section.objects.get(grade="Segundo básico")
    assert seccion.homeroom_teacher_id == maestro.id


@pytest.mark.django_db
def test_seccion_taller_sin_maestro_guia_se_crea_correctamente():
    rol_direccion = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar"})
    direccion = UserFactory(role=rol_direccion)
    ciclo = SchoolCycleFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/sections/",
        {
            "cycle": str(ciclo.public_id),
            "grade": "Taller de panadería",
            "type": Section.TIPO_TALLER,
        },
        format="json",
    )

    assert respuesta.status_code == 201


@pytest.mark.django_db
def test_editar_letra_de_una_seccion_academica_existente():
    rol_direccion = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar"})
    direccion = UserFactory(role=rol_direccion)
    seccion = SectionFactory(grade="Primero básico", letter="A", type=Section.TIPO_ACADEMICA)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.patch(
        f"/api/v1/sections/{seccion.public_id}/", {"letter": "B"}, format="json"
    )

    assert respuesta.status_code == 200
    seccion.refresh_from_db()
    assert seccion.letter == "B"


@pytest.mark.django_db
def test_no_se_puede_convertir_a_taller_una_seccion_con_maestro_guia():
    rol_direccion = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar"})
    direccion = UserFactory(role=rol_direccion)
    rol_guia = RoleFactory(name="Docente con sección a cargo")
    maestro = UserFactory(role=rol_guia)
    seccion = SectionFactory(type=Section.TIPO_ACADEMICA, homeroom_teacher=maestro)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.patch(
        f"/api/v1/sections/{seccion.public_id}/",
        {"type": Section.TIPO_TALLER},
        format="json",
    )

    assert respuesta.status_code == 400
    seccion.refresh_from_db()
    assert seccion.type == Section.TIPO_ACADEMICA
