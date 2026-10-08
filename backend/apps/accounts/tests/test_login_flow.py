import pytest
from django.conf import settings
from rest_framework.test import APIClient

from .factories import RoleFactory, UserFactory


@pytest.mark.django_db
def test_login_exitoso_devuelve_access_y_cookie_de_refresco():
    rol = RoleFactory(permissions={})
    UserFactory(username="con.clave", password="Correcta-Segura-2026", role=rol)

    client = APIClient()
    respuesta = client.post(
        "/api/v1/auth/login/",
        {"username": "con.clave", "password": "Correcta-Segura-2026"},
        format="json",
    )

    assert respuesta.status_code == 200
    assert "access" in respuesta.data
    cookie = respuesta.cookies.get(settings.REFRESH_COOKIE_NAME)
    assert cookie is not None
    assert cookie["httponly"] is True
    assert cookie["samesite"] == settings.REFRESH_COOKIE_SAMESITE


@pytest.mark.django_db
def test_login_con_contrasena_incorrecta_no_revela_si_el_usuario_existe():
    client = APIClient()

    respuesta_usuario_inexistente = client.post(
        "/api/v1/auth/login/",
        {"username": "no.existe", "password": "cualquiera"},
        format="json",
    )
    respuesta_clave_incorrecta = client.post(
        "/api/v1/auth/login/",
        {"username": "no.existe", "password": "otra-cualquiera"},
        format="json",
    )

    assert respuesta_usuario_inexistente.status_code == 401
    assert respuesta_clave_incorrecta.status_code == 401


@pytest.mark.django_db
def test_logout_revoca_la_cookie_de_refresco():
    rol = RoleFactory(permissions={})
    UserFactory(username="para.logout", password="Correcta-Segura-2026", role=rol)

    client = APIClient()
    client.post(
        "/api/v1/auth/login/",
        {"username": "para.logout", "password": "Correcta-Segura-2026"},
        format="json",
    )

    respuesta = client.post("/api/v1/auth/logout/")
    assert respuesta.status_code == 204

    respuesta_refresh = client.post("/api/v1/auth/refresh/")
    assert respuesta_refresh.status_code == 401


@pytest.mark.django_db
def test_contrasena_temporal_bloquea_otros_endpoints_hasta_cambiarla():
    rol = RoleFactory(permissions={"usuarios_roles": "editar"})
    usuario_nuevo = UserFactory(
        username="primer.ingreso",
        password="Temporal-Segura-2026",
        role=rol,
        must_change_password=True,
    )

    client = APIClient()
    client.force_authenticate(user=usuario_nuevo)

    respuesta_bloqueada = client.get("/api/v1/roles/")
    assert respuesta_bloqueada.status_code == 403

    respuesta_cambio = client.post(
        "/api/v1/auth/change-password/",
        {
            "contrasena_actual": "Temporal-Segura-2026",
            "contrasena_nueva": "Definitiva-Aun-Mas-Segura-2026",
        },
        format="json",
    )
    assert respuesta_cambio.status_code == 204

    usuario_nuevo.refresh_from_db()
    assert usuario_nuevo.must_change_password is False
    assert usuario_nuevo.check_password("Definitiva-Aun-Mas-Segura-2026")


@pytest.mark.django_db
def test_cambiar_la_contrasena_por_la_misma_se_rechaza():
    """Hallazgo A-009."""
    usuario = UserFactory(password="Clave-Actual-Segura-2026")
    client = APIClient()
    client.force_authenticate(user=usuario)

    respuesta = client.post(
        "/api/v1/auth/change-password/",
        {
            "contrasena_actual": "Clave-Actual-Segura-2026",
            "contrasena_nueva": "Clave-Actual-Segura-2026",
        },
        format="json",
    )

    assert respuesta.status_code == 400
