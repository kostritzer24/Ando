from datetime import date

from django.utils import timezone

from apps.catalog.models import Section
from apps.students.models import Enrollment

from ..domain.solvency import es_solvente, meses_del_periodo
from ..models import Payment


def calcular_solvencia(*, enrollment, hasta: date | None = None) -> dict:
    """RF-07 / RF-33 / RN-08. `hasta` es la fecha de referencia: por
    omisión, hoy; para las verificaciones de cierre de unidad o de ciclo
    (RN-09), quien llama pasa la fecha de cierre correspondiente."""
    hasta = hasta or timezone.localdate()
    # Un taller no se cobra: su solvencia es la de la inscripción académica
    # del mismo estudiante y ciclo.
    if enrollment.section.type == Section.TIPO_TALLER:
        academica = Enrollment.objects.filter(
            student=enrollment.student,
            cycle=enrollment.cycle,
            section__type=Section.TIPO_ACADEMICA,
            is_active=True,
        ).first()
        if academica is not None:
            enrollment = academica
    tope = min(hasta, enrollment.cycle.end_date)
    meses_esperados = meses_del_periodo(inicio=enrollment.cycle.start_date, hasta=tope)
    meses_pagados = set(
        Payment.objects.filter(
            enrollment=enrollment, concept=Payment.CONCEPTO_MENSUALIDAD, is_active=True
        ).values_list("period_year", "period_month")
    )
    tiene_beca = enrollment.scholarship_id is not None
    inscripcion_pagada = (
        tiene_beca
        or Payment.objects.filter(
            enrollment=enrollment, concept=Payment.CONCEPTO_INSCRIPCION, is_active=True
        ).exists()
    )
    solvente = es_solvente(
        tiene_beca=tiene_beca,
        meses_esperados=meses_esperados,
        meses_pagados=meses_pagados,
        inscripcion_pagada=inscripcion_pagada,
    )
    # Con beca no hay meses "pendientes" que mostrarle a la familia — la
    # beca los cubre, aunque no haya un Payment registrado para esos
    # meses (RN-08: con beca siempre es solvente, sin importar Payment).
    meses_pendientes = set() if tiene_beca else meses_esperados - meses_pagados
    return {
        "solvente": solvente,
        "tiene_beca": tiene_beca,
        "meses_pendientes": sorted(meses_pendientes),
        "inscripcion_pagada": inscripcion_pagada,
    }
