from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.models import Section
from apps.catalog.tests.factories import ScholarshipFactory, SectionFactory
from apps.payments.models import Payment
from apps.students.tests.factories import EnrollmentFactory

pytestmark = pytest.mark.django_db


def _cliente_pagos():
    rol = RoleFactory(name="Encargado de pagos", permissions={"pagos_solvencia": "editar"})
    client = APIClient()
    client.force_authenticate(user=UserFactory(role=rol))
    return client


def _pagar(client, inscripcion, **extra):
    return client.post(
        "/api/v1/payments/",
        {"enrollment": str(inscripcion.public_id), "payment_date": "2026-03-05", **extra},
        format="json",
    )


def test_rf07_la_mensualidad_de_basico_es_q100_y_el_recibo_lo_pone_el_sistema():
    seccion = SectionFactory(grade="Segundo básico")
    inscripcion = EnrollmentFactory(section=seccion, cycle=seccion.cycle)

    # Aunque el cliente mande otro monto y otro recibo, se ignoran.
    respuesta = _pagar(
        _cliente_pagos(),
        inscripcion,
        period_month=3,
        period_year=2026,
        amount="999.00",
        receipt_number="MANUAL-1",
    )

    assert respuesta.status_code == 201, respuesta.data
    assert Decimal(respuesta.data["amount"]) == Decimal("100.00")
    assert respuesta.data["receipt_number"].startswith("REC-2026-")
    assert respuesta.data["receipt_number"] != "MANUAL-1"


def test_rf07_la_mensualidad_de_bachillerato_es_q150():
    seccion = SectionFactory(grade="Cuarto bachillerato")
    inscripcion = EnrollmentFactory(section=seccion, cycle=seccion.cycle)

    respuesta = _pagar(_cliente_pagos(), inscripcion, period_month=3, period_year=2026)

    assert Decimal(respuesta.data["amount"]) == Decimal("150.00")


def test_rf07_dos_pagos_reciben_recibos_distintos():
    seccion = SectionFactory(grade="Segundo básico")
    inscripcion = EnrollmentFactory(section=seccion, cycle=seccion.cycle)
    client = _cliente_pagos()

    uno = _pagar(client, inscripcion, period_month=3, period_year=2026)
    dos = _pagar(client, inscripcion, period_month=4, period_year=2026)

    assert uno.data["receipt_number"] != dos.data["receipt_number"]


def test_rf07_la_inscripcion_es_de_q200_una_sola_vez_por_ciclo():
    seccion = SectionFactory(grade="Segundo básico")
    inscripcion = EnrollmentFactory(section=seccion, cycle=seccion.cycle)
    client = _cliente_pagos()

    primera = _pagar(client, inscripcion, concept="inscripcion")
    segunda = _pagar(client, inscripcion, concept="inscripcion")

    assert primera.status_code == 201, primera.data
    assert Decimal(primera.data["amount"]) == Decimal("200.00")
    assert primera.data["period_month"] is None
    assert segunda.status_code == 400
    assert Payment.objects.filter(concept="inscripcion").count() == 1


def test_rf07_con_beca_completa_no_se_registran_cobros():
    seccion = SectionFactory(grade="Segundo básico")
    inscripcion = EnrollmentFactory(
        section=seccion, cycle=seccion.cycle, scholarship=ScholarshipFactory()
    )

    respuesta = _pagar(_cliente_pagos(), inscripcion, period_month=3, period_year=2026)

    assert respuesta.status_code == 400
    assert "beca" in str(respuesta.data).lower()


def test_rf07_un_taller_no_genera_cobros():
    taller = SectionFactory(grade="Panadería", type=Section.TIPO_TALLER)
    inscripcion = EnrollmentFactory(section=taller, cycle=taller.cycle)

    respuesta = _pagar(_cliente_pagos(), inscripcion, period_month=3, period_year=2026)

    assert respuesta.status_code == 400


def test_rn08_la_solvencia_de_la_inscripcion_de_taller_es_la_de_su_grado():
    from apps.payments.services.solvency import calcular_solvencia
    from apps.students.tests.factories import StudentFactory

    estudiante = StudentFactory()
    grado = SectionFactory(grade="Segundo básico")
    taller = SectionFactory(grade="Panadería", type=Section.TIPO_TALLER, cycle=grado.cycle)
    EnrollmentFactory(
        student=estudiante, section=grado, cycle=grado.cycle, scholarship=ScholarshipFactory()
    )
    inscripcion_taller = EnrollmentFactory(student=estudiante, section=taller, cycle=grado.cycle)

    assert calcular_solvencia(enrollment=inscripcion_taller)["solvente"] is True
