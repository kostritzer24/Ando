import pytest
from django.core.management import call_command

from apps.accounts.models import Role, User
from apps.catalog.models import ConductRuleArticle, GradingUnit, SchoolCycle, Section


@pytest.mark.django_db
def test_seed_demo_crea_roles_usuarios_y_datos_maestros():
    call_command("seed_demo")

    assert Role.objects.count() == 8
    assert User.objects.count() == 8

    ciclo = SchoolCycle.objects.get(year=2026)
    assert GradingUnit.objects.filter(cycle=ciclo).count() == 4
    assert Section.objects.filter(cycle=ciclo).count() == 7
    assert ConductRuleArticle.objects.count() == 16


@pytest.mark.django_db
def test_seed_demo_es_idempotente():
    call_command("seed_demo")
    call_command("seed_demo")

    assert SchoolCycle.objects.filter(year=2026).count() == 1
    assert GradingUnit.objects.filter(cycle__year=2026).count() == 4
    assert Section.objects.filter(cycle__year=2026).count() == 7
    assert ConductRuleArticle.objects.count() == 16
