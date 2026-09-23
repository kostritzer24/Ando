import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import GradingUnit

from .factories import SchoolCycleFactory


@pytest.mark.django_db
def test_rf02_rn10_crear_unidad_calcula_fechas_derivadas():
    rol = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar", "notas": "editar"})
    direccion = UserFactory(role=rol)
    ciclo = SchoolCycleFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        f"/api/v1/cycles/{ciclo.public_id}/units/",
        {"number": 1, "start_date": "2026-01-12", "end_date": "2026-02-28"},
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["grades_due_date"] == "2026-03-15"
    assert respuesta.data["report_card_enabled_date"] == "2026-03-22"


@pytest.mark.django_db
def test_rf02_rn10_no_se_puede_forzar_la_fecha_de_entrega_desde_el_cliente():
    """RN-10: la fecha de entrega de notas se calcula siempre, nunca se
    acepta un valor del cliente que no coincida con la regla."""
    rol = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar", "notas": "editar"})
    direccion = UserFactory(role=rol)
    ciclo = SchoolCycleFactory()

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.post(
        f"/api/v1/cycles/{ciclo.public_id}/units/",
        {
            "number": 1,
            "start_date": "2026-01-12",
            "end_date": "2026-02-28",
            "grades_due_date": "2026-01-01",
            "report_card_enabled_date": "2026-01-02",
        },
        format="json",
    )

    assert respuesta.status_code == 201
    assert respuesta.data["grades_due_date"] == "2026-03-15"
    assert respuesta.data["report_card_enabled_date"] == "2026-03-22"


@pytest.mark.django_db
def test_rf02_rn10_editar_la_fecha_de_cierre_recalcula_las_fechas_derivadas():
    rol = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar", "notas": "editar"})
    direccion = UserFactory(role=rol)
    ciclo = SchoolCycleFactory()
    unidad = GradingUnit.objects.create(
        cycle=ciclo,
        number=1,
        start_date="2026-01-12",
        end_date="2026-02-28",
        grades_due_date="2026-03-15",
        report_card_enabled_date="2026-03-22",
    )

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.patch(
        f"/api/v1/cycles/{ciclo.public_id}/units/{unidad.public_id}/",
        {"end_date": "2026-03-10"},
        format="json",
    )

    assert respuesta.status_code == 200
    assert respuesta.data["grades_due_date"] == "2026-03-25"
    assert respuesta.data["report_card_enabled_date"] == "2026-04-01"
    unidad.refresh_from_db()
    assert unidad.grades_due_date.isoformat() == "2026-03-25"


@pytest.mark.django_db
def test_rf02_unidad_solo_se_lista_dentro_de_su_propio_ciclo():
    rol = RoleFactory(name="Dirección", permissions={"datos_maestros": "editar", "notas": "editar"})
    direccion = UserFactory(role=rol)
    ciclo_uno = SchoolCycleFactory()
    ciclo_dos = SchoolCycleFactory()
    GradingUnit.objects.create(
        cycle=ciclo_uno,
        number=1,
        start_date="2026-01-12",
        end_date="2026-02-28",
        grades_due_date="2026-03-15",
        report_card_enabled_date="2026-03-22",
    )

    client = APIClient()
    client.force_authenticate(user=direccion)

    respuesta = client.get(f"/api/v1/cycles/{ciclo_dos.public_id}/units/")

    assert respuesta.status_code == 200
    assert respuesta.data["count"] == 0
