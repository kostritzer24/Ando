import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.core.permissions import DenyAll, PermisoPorArea


class _VistaDePrueba(APIView):
    area = "notas"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "nivel_rol,metodo,esperado",
    [
        ("ver", "get", True),
        ("ver", "post", False),
        ("editar", "get", True),
        ("editar", "post", True),
        ("sin_acceso", "get", False),
        ("sin_acceso", "post", False),
    ],
)
def test_rnf03_permiso_por_area_respeta_el_nivel_del_rol(nivel_rol, metodo, esperado):
    rol = RoleFactory(permissions={"notas": nivel_rol})
    usuario = UserFactory(role=rol)

    factory = APIRequestFactory()
    django_request = getattr(factory, metodo)("/cualquier-ruta/")
    request = Request(django_request)
    request.user = usuario

    permiso = PermisoPorArea()
    assert permiso.has_permission(request, _VistaDePrueba()) is esperado


@pytest.mark.django_db
def test_rnf03_area_sin_permiso_declarado_se_trata_como_sin_acceso():
    rol = RoleFactory(permissions={})  # "notas" no aparece en el mapa
    usuario = UserFactory(role=rol)

    request = Request(APIRequestFactory().get("/cualquier-ruta/"))
    request.user = usuario

    assert PermisoPorArea().has_permission(request, _VistaDePrueba()) is False


@pytest.mark.django_db
def test_rnf03_usuario_con_contrasena_temporal_sin_cambiar_queda_bloqueado():
    rol = RoleFactory(permissions={"notas": "editar"})
    usuario = UserFactory(role=rol, must_change_password=True)

    request = Request(APIRequestFactory().get("/cualquier-ruta/"))
    request.user = usuario

    assert PermisoPorArea().has_permission(request, _VistaDePrueba()) is False


def test_rnf03_deny_all_niega_siempre():
    request = Request(APIRequestFactory().get("/cualquier-ruta/"))
    assert DenyAll().has_permission(request, _VistaDePrueba()) is False
