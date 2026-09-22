import pytest
from rest_framework.test import APIClient

from .factories import RoleFactory, UserFactory


@pytest.mark.django_db
def test_cualquier_usuario_autenticado_consulta_su_propio_perfil():
    """GET /auth/me/ no pasa por el área "Usuarios y roles" (exclusiva de
    Dirección/Administrador) — es sobre la identidad propia, no sobre
    administrar cuentas ajenas."""
    rol = RoleFactory(name="Tallerista", permissions={})
    usuario = UserFactory(username="tallerista.prueba", role=rol)
    client = APIClient()
    client.force_authenticate(user=usuario)

    respuesta = client.get("/api/v1/auth/me/")

    assert respuesta.status_code == 200
    assert respuesta.data["username"] == "tallerista.prueba"
    assert respuesta.data["role_name"] == "Tallerista"


@pytest.mark.django_db
def test_un_usuario_con_cambio_de_contrasena_pendiente_tambien_puede_consultarse():
    """El frontend necesita saber `must_change_password` para decidir a
    dónde mandar a la persona apenas se restaura la sesión — esta ruta no
    puede quedar bloqueada por esa misma condición."""
    rol = RoleFactory(permissions={})
    usuario = UserFactory(must_change_password=True, role=rol)
    client = APIClient()
    client.force_authenticate(user=usuario)

    respuesta = client.get("/api/v1/auth/me/")

    assert respuesta.status_code == 200
    assert respuesta.data["must_change_password"] is True


@pytest.mark.django_db
def test_sin_sesion_da_401():
    client = APIClient()
    respuesta = client.get("/api/v1/auth/me/")
    assert respuesta.status_code == 401
