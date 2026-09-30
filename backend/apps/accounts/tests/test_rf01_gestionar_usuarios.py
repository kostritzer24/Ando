import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.core.models import AuditLog

from .factories import RoleFactory, UserFactory


@pytest.fixture
def admin():
    rol = RoleFactory(name="Administrador del sistema", permissions={"usuarios_roles": "editar"})
    return UserFactory(username="admin.prueba", role=rol)


@pytest.fixture
def cliente(admin):
    client = APIClient()
    client.force_authenticate(user=admin)
    return client


@pytest.mark.django_db
def test_rf01_editar_nombre_y_rol_deja_bitacora_con_valor_anterior_y_nuevo(cliente):
    docente = RoleFactory(name="Docente")
    guia = RoleFactory(name="Docente con sección a cargo")
    persona = UserFactory(username="p.lopez", first_name="Pedro", role=docente)

    respuesta = cliente.patch(
        f"/api/v1/users/{persona.public_id}/",
        {"first_name": "Pedro José", "role": str(guia.public_id)},
        format="json",
    )

    assert respuesta.status_code == 200
    persona.refresh_from_db()
    assert persona.first_name == "Pedro José"
    assert persona.role == guia
    registro = AuditLog.objects.get(entity_name="accounts.User", entity_id=persona.id)
    assert registro.old_value == {"first_name": "Pedro", "role": "Docente"}
    assert registro.new_value == {"first_name": "Pedro José", "role": "Docente con sección a cargo"}


@pytest.mark.django_db
def test_rf01_desactivar_una_cuenta_le_impide_entrar(cliente):
    persona = UserFactory(
        username="se.va", password="Correcta-Segura-2026", role=RoleFactory(name="Docente")
    )

    respuesta = cliente.patch(
        f"/api/v1/users/{persona.public_id}/", {"is_active": False}, format="json"
    )

    assert respuesta.status_code == 200
    login = APIClient().post(
        "/api/v1/auth/login/", {"username": "se.va", "password": "Correcta-Segura-2026"}
    )
    assert login.status_code == 401


@pytest.mark.django_db
def test_rf01_nadie_se_desactiva_ni_se_cambia_el_rol_a_si_mismo(cliente, admin):
    otro_rol = RoleFactory(name="Docente")

    desactivar = cliente.patch(
        f"/api/v1/users/{admin.public_id}/", {"is_active": False}, format="json"
    )
    cambiar_rol = cliente.patch(
        f"/api/v1/users/{admin.public_id}/", {"role": str(otro_rol.public_id)}, format="json"
    )

    assert desactivar.status_code == 400
    assert cambiar_rol.status_code == 400
    admin.refresh_from_db()
    assert admin.is_active is True


@pytest.mark.django_db
def test_rf01_una_cuenta_nunca_se_borra_de_verdad(cliente):
    persona = UserFactory(username="no.se.borra", role=RoleFactory(name="Docente"))

    respuesta = cliente.delete(f"/api/v1/users/{persona.public_id}/")

    assert respuesta.status_code == 405
    assert User.objects.filter(username="no.se.borra").exists()


@pytest.mark.django_db
def test_rf01_el_nombre_de_usuario_no_se_cambia_al_editar(cliente):
    persona = UserFactory(username="fijo", role=RoleFactory(name="Docente"))

    cliente.patch(f"/api/v1/users/{persona.public_id}/", {"username": "otro"}, format="json")

    persona.refresh_from_db()
    assert persona.username == "fijo"


@pytest.mark.django_db
def test_rnf03_los_roles_no_se_editan_ni_se_borran_desde_la_api(cliente):
    rol = RoleFactory(name="Docente", permissions={"notas": "editar"})

    editar = cliente.patch(f"/api/v1/roles/{rol.public_id}/", {"permissions": {}}, format="json")
    borrar = cliente.delete(f"/api/v1/roles/{rol.public_id}/")

    assert editar.status_code == 405
    assert borrar.status_code == 405
    assert Role.objects.get(pk=rol.pk).permissions == {"notas": "editar"}


@pytest.mark.django_db
def test_rf01_coordinacion_no_puede_editar_usuarios_acceso_no_autorizado():
    coordinacion = UserFactory(
        role=RoleFactory(name="Coordinación", permissions={"usuarios_roles": "sin_acceso"})
    )
    persona = UserFactory(username="intocable", role=RoleFactory(name="Docente"))
    client = APIClient()
    client.force_authenticate(user=coordinacion)

    respuesta = client.patch(
        f"/api/v1/users/{persona.public_id}/", {"is_active": False}, format="json"
    )

    assert respuesta.status_code == 403
    persona.refresh_from_db()
    assert persona.is_active is True


@pytest.mark.django_db
def test_rnf03_auth_me_devuelve_los_permisos_del_rol():
    permisos = {"notas": "ver", "asistencia": "editar"}
    persona = UserFactory(role=RoleFactory(name="Coordinación", permissions=permisos))
    client = APIClient()
    client.force_authenticate(user=persona)

    respuesta = client.get("/api/v1/auth/me/")

    assert respuesta.data["permissions"] == permisos


@pytest.mark.django_db
def test_rnf03_el_login_devuelve_los_permisos_del_rol():
    permisos = {"usuarios_roles": "editar"}
    UserFactory(
        username="con.permisos",
        password="Correcta-Segura-2026",
        role=RoleFactory(name="Administrador del sistema", permissions=permisos),
    )

    respuesta = APIClient().post(
        "/api/v1/auth/login/", {"username": "con.permisos", "password": "Correcta-Segura-2026"}
    )

    assert respuesta.data["user"]["permissions"] == permisos
