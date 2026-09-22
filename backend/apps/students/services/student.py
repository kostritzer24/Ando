from datetime import date

from django.db import transaction

from ..domain.internal_code import generar_codigo_interno
from ..models import Student


def _siguiente_numero_secuencial() -> int:
    # Válido para el volumen de este centro (144 estudiantes en la
    # jornada matutina, sección 1 del prompt maestro): la administración
    # inscribe estudiantes uno a la vez, no hace falta select_for_update
    # para una operación de este volumen y concurrencia.
    return Student.objects.count() + 1


@transaction.atomic
def crear_estudiante(
    *,
    first_name: str,
    last_name: str,
    birth_date: date,
    address: str = "",
    previous_institution: str = "",
) -> Student:
    """RF-03 / RN-14: el código interno lo asigna siempre el sistema."""
    codigo = generar_codigo_interno(_siguiente_numero_secuencial())
    return Student.objects.create(
        internal_code=codigo,
        first_name=first_name,
        last_name=last_name,
        birth_date=birth_date,
        address=address,
        previous_institution=previous_institution,
    )


def actualizar_datos_sensibles(
    estudiante: Student, *, health_notes: str | None = None, socioeconomic_notes: str | None = None
) -> Student:
    """RNF-04: solo Dirección llega hasta acá — lo hace cumplir el permiso
    del área 'datos_sensibles' en la vista, no esta función."""
    campos = []
    if health_notes is not None:
        estudiante.health_notes = health_notes
        campos.append("health_notes")
    if socioeconomic_notes is not None:
        estudiante.socioeconomic_notes = socioeconomic_notes
        campos.append("socioeconomic_notes")
    if campos:
        estudiante.save(update_fields=[*campos, "updated_at"])
    return estudiante
