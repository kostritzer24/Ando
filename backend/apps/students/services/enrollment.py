from datetime import date

from apps.catalog.models import Scholarship, SchoolCycle, Section

from ..models import Enrollment, Student


class YaInscritoEnEsteCiclo(Exception):
    pass


def inscribir_estudiante(
    *,
    student: Student,
    section: Section,
    cycle: SchoolCycle,
    enrolled_at: date,
    scholarship: Scholarship | None = None,
) -> Enrollment:
    """RF-03 / HU-03: no se puede inscribir dos veces al mismo estudiante
    en el mismo ciclo — se valida acá con un mensaje claro, además de la
    restricción de base de datos que existe como última defensa."""
    if Enrollment.objects.filter(student=student, cycle=cycle, is_active=True).exists():
        raise YaInscritoEnEsteCiclo(f"{student} ya está inscrito en el ciclo {cycle}.")
    return Enrollment.objects.create(
        student=student,
        section=section,
        cycle=cycle,
        scholarship=scholarship,
        enrolled_at=enrolled_at,
    )
