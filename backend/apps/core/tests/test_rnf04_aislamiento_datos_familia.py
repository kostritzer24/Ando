"""
RNF-04 ("cada familia ve solo a sus estudiantes") todavía no tiene
`Student`/`Guardian` en esta fase (llegan en la Fase 5), así que esta
prueba verifica la pieza que hace cumplir la regla en TODAS las apps
futuras: `ScopedQuerysetMixin` filtra siempre desde el usuario hacia el
queryset, nunca al revés. Se ejercita contra `accounts.User` como
modelo de fixture — ver docs/fase-3-cimientos-plan.md, sección 9.
"""

import pytest
from rest_framework import viewsets

from apps.accounts.models import User
from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.core.api.mixins import ScopedQuerysetMixin


class _SoloMiPropioRolViewSet(ScopedQuerysetMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()

    def scope_queryset(self, queryset, user):
        return queryset.filter(role=user.role)


class _ViewSetSinImplementarAlcance(ScopedQuerysetMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()


class _RequestFalso:
    def __init__(self, user):
        self.user = user


@pytest.mark.django_db
def test_rnf04_scoped_queryset_excluye_registros_de_otro_usuario():
    rol_propio = RoleFactory()
    rol_ajeno = RoleFactory()
    propio = UserFactory(role=rol_propio)
    companero = UserFactory(role=rol_propio)
    ajeno = UserFactory(role=rol_ajeno)

    vista = _SoloMiPropioRolViewSet()
    vista.request = _RequestFalso(user=propio)

    resultado = list(vista.get_queryset())

    assert propio in resultado
    assert companero in resultado
    assert ajeno not in resultado


def test_rnf04_scoped_queryset_exige_implementar_el_alcance():
    """Si una vista futura olvida implementar `scope_queryset`, falla en
    vez de devolver el queryset completo sin filtrar — falla cerrado."""
    vista = _ViewSetSinImplementarAlcance()
    vista.request = _RequestFalso(user=None)
    with pytest.raises(NotImplementedError):
        vista.get_queryset()
