from datetime import date

from django.utils import timezone

from ..domain.solvency import es_solvente, meses_del_periodo
from ..models import Payment


def calcular_solvencia(*, enrollment, hasta: date | None = None) -> dict:
    """RF-07 / RF-33 / RN-08. `hasta` es la fecha de referencia: por
    omisión, hoy; para las verificaciones de cierre de unidad o de ciclo
    (RN-09), quien llama pasa la fecha de cierre correspondiente."""
    hasta = hasta or timezone.localdate()
    tope = min(hasta, enrollment.cycle.end_date)
    meses_esperados = meses_del_periodo(inicio=enrollment.cycle.start_date, hasta=tope)
    meses_pagados = set(
        Payment.objects.filter(enrollment=enrollment, is_active=True).values_list(
            "period_year", "period_month"
        )
    )
    tiene_beca = enrollment.scholarship_id is not None
    solvente = es_solvente(
        tiene_beca=tiene_beca, meses_esperados=meses_esperados, meses_pagados=meses_pagados
    )
    # Con beca no hay meses "pendientes" que mostrarle a la familia — la
    # beca los cubre, aunque no haya un Payment registrado para esos
    # meses (RN-08: con beca siempre es solvente, sin importar Payment).
    meses_pendientes = set() if tiene_beca else meses_esperados - meses_pagados
    return {
        "solvente": solvente,
        "tiene_beca": tiene_beca,
        "meses_pendientes": sorted(meses_pendientes),
    }
