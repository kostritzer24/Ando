import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_healthz_responde_sin_sesion_para_la_plataforma_de_despliegue():
    respuesta = APIClient().get("/healthz")

    assert respuesta.status_code == 200
