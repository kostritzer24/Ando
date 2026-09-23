import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_seccion14_4_toda_respuesta_trae_content_security_policy():
    respuesta = APIClient().post("/api/v1/auth/login/", {}, format="json")

    assert "Content-Security-Policy" in respuesta
    assert "default-src 'self'" in respuesta["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in respuesta["Content-Security-Policy"]
