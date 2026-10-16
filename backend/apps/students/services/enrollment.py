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

    # Si el estudiante estuvo en esa sección y se le dio de baja, volver a
    # inscribirlo reactiva la inscripción anterior (la restricción de
    # unicidad cuenta también las dadas de baja).
    previa = Enrollment.objects.filter(student=student, cycle=cycle, section=section).first()
    if previa is not None:
        previa.is_active = True
        previa.status = Enrollment.ESTADO_ACTIVO
        previa.scholarship = scholarship
        previa.enrolled_at = enrolled_at
        previa.save(
            update_fields=["is_active", "status", "scholarship", "enrolled_at", "updated_at"]
        )
        return previa

    return Enrollment.objects.create(
        student=student,
        section=section,
        cycle=cycle,
        scholarship=scholarship,
        enrolled_at=enrolled_at,
    )


class CambioDeSeccionInvalido(Exception):
    pass


def cambiar_seccion(*, enrollment: Enrollment, section: Section) -> Enrollment:
    """Mueve la inscripción a otra sección del mismo ciclo y del mismo
    tipo (de un grado a otro grado, de un taller a otro taller), sin
    crear un estudiante ni una inscripción nueva: el historial de pagos,
    asistencia y notas se queda con ella."""
    if section.id == enrollment.section_id:
        return enrollment
    if section.cycle_id != enrollment.cycle_id:
        raise CambioDeSeccionInvalido("La sección nueva debe ser del mismo ciclo escolar.")
    if section.type != enrollment.section.type:
        raise CambioDeSeccionInvalido(
            "Una inscripción de grado solo cambia a otro grado, y una de taller a otro taller."
        )
    if Enrollment.objects.filter(
        student=enrollment.student, cycle=enrollment.cycle, section=section
    ).exists():
        raise CambioDeSeccionInvalido(f"El estudiante ya está inscrito en {section}.")
    enrollment.section = section
    enrollment.save(update_fields=["section", "updated_at"])
    return enrollment
