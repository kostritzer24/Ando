from datetime import date

from apps.catalog.models import Scholarship, SchoolCycle, Section

from ..models import Enrollment, Student


class YaInscritoEnEsaSeccion(Exception):
    pass


class YaTieneSeccionAcademicaEnEsteCiclo(Exception):
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
    en la misma sección. Un estudiante puede tener a la vez su
    inscripción académica y una o varias de taller en el mismo ciclo
    (sección 1 del prompt maestro: los participantes de taller son, al
    menos en parte, los mismos estudiantes de la jornada matutina) —
    pero solo una sección académica por ciclo."""
    if Enrollment.objects.filter(
        student=student, cycle=cycle, section=section, is_active=True
    ).exists():
        raise YaInscritoEnEsaSeccion(
            f"{student} ya está inscrito en {section} en el ciclo {cycle}."
        )

    if (
        section.type == Section.TIPO_ACADEMICA
        and Enrollment.objects.filter(
            student=student, cycle=cycle, section__type=Section.TIPO_ACADEMICA, is_active=True
        ).exists()
    ):
        raise YaTieneSeccionAcademicaEnEsteCiclo(
            f"{student} ya tiene una sección académica en el ciclo {cycle}."
        )

    return Enrollment.objects.create(
        student=student,
        section=section,
        cycle=cycle,
        scholarship=scholarship,
        enrolled_at=enrolled_at,
    )
