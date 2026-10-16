from apps.catalog.models import Course, SchoolCycle, Section

from ..domain.teacher_assignment import AsignacionInvalida, validar_asignacion
from ..models import ScheduleBlock, TeacherAssignment


def crear_asignacion(
    *, teacher, course: Course, section: Section, cycle: SchoolCycle
) -> TeacherAssignment:
    validar_asignacion(
        course_type=course.type, section_type=section.type, teacher_role_name=teacher.role.name
    )
    previa = TeacherAssignment.objects.filter(
        teacher=teacher, course=course, section=section, cycle=cycle
    ).first()
    if previa is not None:
        if previa.is_active:
            raise AsignacionInvalida(
                f"{teacher.nombre_completo()} ya tiene asignado {course.name} en esa sección."
            )
        # Una asignación dada de baja se reactiva (sus clases del horario
        # no vuelven: hay que armarlas de nuevo).
        previa.is_active = True
        previa.save(update_fields=["is_active", "updated_at"])
        return previa
    return TeacherAssignment.objects.create(
        teacher=teacher, course=course, section=section, cycle=cycle
    )


def dar_de_baja_asignacion(asignacion: TeacherAssignment) -> None:
    """Baja lógica: sus clases del horario dejan de ocupar celdas."""
    ScheduleBlock.objects.filter(assignment=asignacion, is_active=True).update(is_active=False)
    asignacion.is_active = False
    asignacion.save(update_fields=["is_active", "updated_at"])
