"""Sección 11 del prompt maestro: métricas del estudio, con corte
semanal (últimos 7 días) y sin exponer información personal — nunca un
identificador de estudiante, encargado o docente, solo conteos
agregados. Dos indicadores, cada uno con su fórmula documentada porque
el prompt maestro no la fija:

- **Procesos administrativos gestionados por el sistema:** de seis
  categorías de proceso del centro (asistencia, notas, pagos,
  documentos emitidos, boletines, reportes de conducta), cuántas
  tuvieron al menos un registro esta semana. Todo proceso del centro ya
  pasa por el sistema (no hay otro canal en paralelo), así que esto
  mide qué tan completo es el uso semana a semana, no una comparación
  contra un proceso en papel.
- **Encargados que consultan el portal:** de los usuarios activos con
  rol "Padre de familia", qué porcentaje tiene al menos un acceso
  registrado (RNF-07) esta semana.
"""

from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.attendance.models import Attendance
from apps.communication.models import ConductReport
from apps.core.models import AccessLog
from apps.documents.models import IssuedDocument
from apps.grading.models import Grade, ReportCard
from apps.payments.models import Payment

ROL_FAMILIA = "Padre de familia"


def metricas_semanales() -> dict:
    desde = timezone.now() - timedelta(days=7)

    procesos = {
        "asistencia": Attendance.objects.filter(created_at__gte=desde).exists(),
        "notas": Grade.objects.filter(created_at__gte=desde).exists(),
        "pagos": Payment.objects.filter(created_at__gte=desde).exists(),
        "documentos_emitidos": IssuedDocument.objects.filter(issued_at__gte=desde).exists(),
        "boletines": ReportCard.objects.filter(published_at__gte=desde).exists(),
        "reportes_conducta": ConductReport.objects.filter(created_at__gte=desde).exists(),
    }
    procesos_gestionados = sum(1 for ok in procesos.values() if ok)

    encargados_activos = User.objects.filter(role__name=ROL_FAMILIA, is_active=True).count()
    encargados_con_acceso = (
        AccessLog.objects.filter(user__role__name=ROL_FAMILIA, accessed_at__gte=desde)
        .values("user_id")
        .distinct()
        .count()
    )

    return {
        "period_start": desde,
        "period_end": timezone.now(),
        "administrative_processes_percentage": round(procesos_gestionados / len(procesos) * 100),
        "guardians_portal_usage_percentage": (
            round(encargados_con_acceso / encargados_activos * 100) if encargados_activos else 0
        ),
    }
