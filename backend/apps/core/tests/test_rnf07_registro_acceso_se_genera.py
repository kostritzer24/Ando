import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.core.models import AccessLog
from apps.core.services import registrar_acceso


@pytest.mark.django_db
def test_rnf07_registrar_acceso_crea_un_registro():
    usuario = UserFactory()
    registro = registrar_acceso(usuario=usuario, pantalla="/api/v1/roles/")
    assert AccessLog.objects.filter(
        pk=registro.pk, user=usuario, screen_viewed="/api/v1/roles/"
    ).exists()


@pytest.mark.django_db
def test_rnf07_peticion_autenticada_a_la_api_genera_registro_de_acceso():
    rol = RoleFactory(permissions={"usuarios_roles": "ver"})
    usuario = UserFactory(role=rol)

    client = APIClient()
    client.force_authenticate(user=usuario)
    client.get("/api/v1/roles/")

    assert AccessLog.objects.filter(user=usuario, screen_viewed="/api/v1/roles/").exists()


@pytest.mark.django_db
def test_rnf07_peticion_anonima_no_genera_registro_de_acceso():
    client = APIClient()
    client.get("/api/v1/roles/")
    assert not AccessLog.objects.exists()
