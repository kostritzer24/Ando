from datetime import date

import pytest
from rest_framework.test import APIClient

from apps.accounts.tests.factories import RoleFactory, UserFactory
from apps.catalog.tests.factories import ScholarshipFactory, SchoolCycleFactory
from apps.core.models import AuditLog
from apps.payments.models import Payment
from apps.payments.services.solvency import calcular_solvencia
from apps.students.services.link import vincular_encargado_estudiante
from apps.students.tests.factories import EnrollmentFactory, GuardianFactory, StudentFactory

from .factories import PaymentFactory


@pytest.mark.django_db
def test_rn08_solvente_cuando_estan_pagados_todos_los_meses_del_periodo():
    ciclo = SchoolCycleFactory(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    inscripcion = EnrollmentFactory(cycle=ciclo)
    PaymentFactory(enrollment=inscripcion, period_year=2026, period_month=1)
    PaymentFactory(enrollment=inscripcion, period_year=2026, period_month=2)

    resultado = calcular_solvencia(enrollment=inscripcion, hasta=date(2026, 2, 15))

    assert resultado == {"solvente": True, "tiene_beca": False, "meses_pendientes": []}


@pytest.mark.django_db
def test_rn08_insolvente_si_falta_un_mes_pasado():
    ciclo = SchoolCycleFactory(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    inscripcion = EnrollmentFactory(cycle=ciclo)
    PaymentFactory(enrollment=inscripcion, period_year=2026, period_month=1)
    # Febrero se salta.

    resultado = calcular_solvencia(enrollment=inscripcion, hasta=date(2026, 3, 1))

    assert resultado["solvente"] is False
    assert resultado["meses_pendientes"] == [(2026, 2), (2026, 3)]


@pytest.mark.django_db
def test_rn08_con_beca_es_solvente_sin_pagos():
    ciclo = SchoolCycleFactory(start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    beca = ScholarshipFactory()
    inscripcion = EnrollmentFactory(cycle=ciclo, scholarship=beca)

    resultado = calcular_solvencia(enrollment=inscripcion, hasta=date(2026, 6, 1))

    assert resultado == {"solvente": True, "tiene_beca": True, "meses_pendientes": []}


@pytest.mark.django_db
def test_rf07_registrar_pago_deja_rastro_en_la_bitacora_rnf06():
    rol_pagos = RoleFactory(name="Encargado de pagos", permissions={"pagos_solvencia": "editar"})
    usuario_pagos = UserFactory(role=rol_pagos)
    inscripcion = EnrollmentFactory()

    client = APIClient()
    client.force_authenticate(user=usuario_pagos)

    respuesta = client.post(
        "/api/v1/payments/",
        {
            "enrollment": str(inscripcion.public_id),
            "period_month": 3,
            "period_year": 2026,
            "amount": "150.00",
            "payment_date": "2026-03-05",
            "receipt_number": "R-00001",
        },
    )

    assert respuesta.status_code == 201, respuesta.data
    pago = Payment.objects.get(receipt_number="R-00001")
    assert AuditLog.objects.filter(
        entity_name="Payment", entity_id=pago.id, action="crear"
    ).exists()


@pytest.mark.django_db
def test_rf07_no_se_puede_registrar_dos_pagos_del_mismo_mes():
    rol_pagos = RoleFactory(name="Encargado de pagos", permissions={"pagos_solvencia": "editar"})
    usuario_pagos = UserFactory(role=rol_pagos)
    inscripcion = EnrollmentFactory()
    PaymentFactory(enrollment=inscripcion, period_year=2026, period_month=4, receipt_number="R-1")

    client = APIClient()
    client.force_authenticate(user=usuario_pagos)

    respuesta = client.post(
        "/api/v1/payments/",
        {
            "enrollment": str(inscripcion.public_id),
            "period_month": 4,
            "period_year": 2026,
            "amount": "150.00",
            "payment_date": "2026-04-05",
            "receipt_number": "R-2",
        },
    )

    assert respuesta.status_code == 400


@pytest.mark.django_db
def test_rf33_familia_consulta_la_solvencia_de_su_propio_estudiante():
    rol_familia = RoleFactory(name="Padre de familia", permissions={"pagos_solvencia": "ver"})
    usuario_familia = UserFactory(role=rol_familia)
    encargado = GuardianFactory(user=usuario_familia)
    beca = ScholarshipFactory()
    mi_hijo = StudentFactory(internal_code="ES010")
    vincular_encargado_estudiante(guardian=encargado, student=mi_hijo, relationship="Madre")
    mi_inscripcion = EnrollmentFactory(student=mi_hijo, scholarship=beca)

    client = APIClient()
    client.force_authenticate(user=usuario_familia)

    respuesta = client.get(f"/api/v1/solvency/{mi_inscripcion.public_id}/")

    assert respuesta.status_code == 200
    assert respuesta.data["solvente"] is True


@pytest.mark.django_db
def test_rf33_familia_no_alcanza_la_solvencia_de_un_estudiante_ajeno_acceso_no_autorizado():
    """El alcance se filtra en el queryset antes del 404 (sección 14.2):
    cambiar el UUID en la URL no confirma que la inscripción exista."""
    rol_familia = RoleFactory(name="Padre de familia", permissions={"pagos_solvencia": "ver"})
    usuario_familia = UserFactory(role=rol_familia)
    GuardianFactory(user=usuario_familia)
    inscripcion_ajena = EnrollmentFactory()

    client = APIClient()
    client.force_authenticate(user=usuario_familia)

    respuesta = client.get(f"/api/v1/solvency/{inscripcion_ajena.public_id}/")

    assert respuesta.status_code == 404


@pytest.mark.django_db
def test_docente_no_alcanza_pagos_y_solvencia_acceso_no_autorizado():
    rol_docente = RoleFactory(name="Docente", permissions={"pagos_solvencia": "sin_acceso"})
    docente = UserFactory(role=rol_docente)
    inscripcion = EnrollmentFactory()

    client = APIClient()
    client.force_authenticate(user=docente)

    respuesta = client.get(f"/api/v1/solvency/{inscripcion.public_id}/")

    assert respuesta.status_code == 403
