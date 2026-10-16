import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import Section

from .factories import SchoolCycleFactory, SectionFactory

pytestmark = pytest.mark.django_db


def _direccion_client():
    rol = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar"})
    client = APIClient()
    client.force_authenticate(user=UserFactory(role=rol))
    return client


def _datos(ciclo, grado="Quinto bachillerato", letra="A"):
    return {
        "cycle": str(ciclo.public_id),
        "grade": grado,
        "letter": letra,
        "type": Section.TIPO_ACADEMICA,
    }


def test_rf02_no_se_puede_repetir_una_seccion_en_el_mismo_ciclo():
    ciclo = SchoolCycleFactory()
    SectionFactory(cycle=ciclo, grade="Quinto bachillerato", letter="A")

    respuesta = _direccion_client().post(
        "/api/v1/sections/", _datos(ciclo, "quinto bachillerato "), format="json"
    )

    assert respuesta.status_code == 400
    assert Section.objects.filter(cycle=ciclo).count() == 1


def test_rf02_la_misma_seccion_en_otro_ciclo_o_con_otra_letra_si_se_puede():
    ciclo = SchoolCycleFactory()
    otro_ciclo = SchoolCycleFactory()
    SectionFactory(cycle=ciclo, grade="Quinto bachillerato", letter="A")
    client = _direccion_client()

    assert client.post("/api/v1/sections/", _datos(otro_ciclo), format="json").status_code == 201
    assert (
        client.post("/api/v1/sections/", _datos(ciclo, letra="B"), format="json").status_code == 201
    )


def test_rf02_una_seccion_dada_de_baja_no_bloquea_crearla_de_nuevo():
    ciclo = SchoolCycleFactory()
    SectionFactory(cycle=ciclo, grade="Quinto bachillerato", letter="A", is_active=False)

    respuesta = _direccion_client().post("/api/v1/sections/", _datos(ciclo), format="json")

    assert respuesta.status_code == 201
