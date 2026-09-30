import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.students.tests.factories import StudentFactory


@pytest.fixture
def cliente_direccion():
    rol = RoleFactory(name="Dirección", permissions={"estudiantes_encargados": "editar"})
    client = APIClient()
    client.force_authenticate(user=UserFactory(role=rol))
    return client


@pytest.mark.django_db
def test_rf03_lista_de_estudiantes_pagina_de_25_por_omision(cliente_direccion):
    StudentFactory.create_batch(30)

    respuesta = cliente_direccion.get("/api/v1/students/")

    assert respuesta.data["count"] == 30
    assert len(respuesta.data["results"]) == 25
    assert respuesta.data["next"] is not None


@pytest.mark.django_db
def test_rf03_lista_de_estudiantes_completa_con_page_size(cliente_direccion):
    StudentFactory.create_batch(30)

    respuesta = cliente_direccion.get("/api/v1/students/", {"page_size": 200})

    assert len(respuesta.data["results"]) == 30
    assert respuesta.data["next"] is None


@pytest.mark.django_db
def test_rf03_page_size_no_supera_el_maximo(cliente_direccion):
    StudentFactory.create_batch(205)

    respuesta = cliente_direccion.get("/api/v1/students/", {"page_size": 1000})

    assert len(respuesta.data["results"]) == 200
    assert respuesta.data["next"] is not None
