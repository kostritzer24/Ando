import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User

from .factories import RoleFactory, UserFactory


@pytest.mark.django_db
def test_rf01_direccion_crea_usuario_y_le_asigna_rol():
    rol_direccion = RoleFactory(name="Dirección", permissions={"usuarios_roles": "editar"})
    rol_docente = RoleFactory(name="Docente", permissions={})
    direccion = UserFactory(role=rol_direccion)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/users/",
        {
            "username": "nuevo.docente",
            "role": str(rol_docente.public_id),
            "contrasena_temporal": "Temporal-Segura-2026",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    usuario_creado = User.objects.get(username="nuevo.docente")
    assert usuario_creado.role_id == rol_docente.id
    assert usuario_creado.must_change_password is True
    assert usuario_creado.check_password("Temporal-Segura-2026")


@pytest.mark.django_db
def test_rf01_no_se_puede_repetir_nombre_de_usuario():
    rol_direccion = RoleFactory(name="Dirección", permissions={"usuarios_roles": "editar"})
    rol_docente = RoleFactory(name="Docente")
    direccion = UserFactory(role=rol_direccion)
    UserFactory(username="ya.existe", role=rol_docente)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        "/api/v1/users/",
        {
            "username": "ya.existe",
            "role": str(rol_docente.public_id),
            "contrasena_temporal": "Temporal-Segura-2026",
        },
        format="json",
    )

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_rf01_docente_no_puede_crear_usuarios_acceso_no_autorizado():
    """Caso de acceso no autorizado (sección 16): un rol sin permiso en
    `usuarios_roles` no puede crear cuentas, aunque esté autenticado."""
    rol_docente = RoleFactory(name="Docente", permissions={"usuarios_roles": "sin_acceso"})
    rol_objetivo = RoleFactory(name="Tallerista")
    docente = UserFactory(role=rol_docente)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        "/api/v1/users/",
        {
            "username": "intento.no.autorizado",
            "role": str(rol_objetivo.public_id),
            "contrasena_temporal": "Temporal-Segura-2026",
        },
        format="json",
    )

    assert respuesta.status_code == 403
    assert not User.objects.filter(username="intento.no.autorizado").exists()


@pytest.mark.django_db
def test_rf01_usuario_no_autenticado_no_puede_crear_usuarios():
    client = APIClient()
    respuesta = client.post("/api/v1/users/", {}, format="json")
    assert respuesta.status_code in (401, 403)
