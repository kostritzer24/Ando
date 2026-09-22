import pytest
from django.core.management import call_command

from apps.accounts.models import Role, User
from apps.catalog.models import ConductRuleArticle, GradingUnit, SchoolCycle, Section
from apps.scheduling.models import TeacherAssignment
from apps.students.models import Enrollment, Guardian, GuardianStudentLink, Student


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
def test_seed_demo_crea_expedientes_y_asignaciones():
    call_command("seed_demo")

    assert Student.objects.count() == 4
    # 5, no 4: el primer estudiante queda inscrito en su sección
    # académica y también en el taller (ver ADR-0001, corrección Fase 6).
    assert Enrollment.objects.count() == 5
    assert Guardian.objects.count() == 1
    assert GuardianStudentLink.objects.filter(is_active=True).count() == 1
    assert TeacherAssignment.objects.count() == 2


@pytest.mark.django_db
def test_seed_demo_es_idempotente():
    call_command("seed_demo")
    call_command("seed_demo")

    assert SchoolCycle.objects.filter(year=2026).count() == 1
    assert GradingUnit.objects.filter(cycle__year=2026).count() == 4
    assert Section.objects.filter(cycle__year=2026).count() == 7
    assert ConductRuleArticle.objects.count() == 16
    assert Student.objects.count() == 4
    assert TeacherAssignment.objects.count() == 2
