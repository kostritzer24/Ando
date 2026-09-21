import pytest
from rest_framework.test import APIClient

from .factories import RoleFactory, UserFactory


@pytest.mark.django_db
def test_direccion_restablece_contrasena_de_un_usuario():
    rol_direccion = RoleFactory(name="Dirección", permissions={"usuarios_roles": "editar"})
    usuario_objetivo = UserFactory(password="Anterior-Segura-2026", must_change_password=False)
    direccion = UserFactory(role=rol_direccion)

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        f"/api/v1/users/{usuario_objetivo.public_id}/reset-password/",
        {"contrasena_temporal": "Nueva-Temporal-Segura-2026"},
        format="json",
    )

    assert respuesta.status_code == 204
    usuario_objetivo.refresh_from_db()
    assert usuario_objetivo.must_change_password is True
    assert usuario_objetivo.check_password("Nueva-Temporal-Segura-2026")


@pytest.mark.django_db
def test_docente_no_puede_restablecer_contrasenas_ajenas():
    rol_docente = RoleFactory(name="Docente", permissions={"usuarios_roles": "sin_acceso"})
    usuario_objetivo = UserFactory(password="Anterior-Segura-2026")
    docente = UserFactory(role=rol_docente)

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.post(
        f"/api/v1/users/{usuario_objetivo.public_id}/reset-password/",
        {"contrasena_temporal": "Nueva-Temporal-Segura-2026"},
        format="json",
    )

    assert respuesta.status_code == 403
    usuario_objetivo.refresh_from_db()
    assert usuario_objetivo.check_password("Anterior-Segura-2026")
