from apps.catalog.models import Course, SchoolCycle, Section

from ..domain.teacher_assignment import validar_asignacion
from ..models import TeacherAssignment


def crear_asignacion(
    *, teacher, course: Course, section: Section, cycle: SchoolCycle
) -> TeacherAssignment:
    validar_asignacion(
        course_type=course.type, section_type=section.type, teacher_role_name=teacher.role.name
    )
    return TeacherAssignment.objects.create(
        teacher=teacher, course=course, section=section, cycle=cycle
    )
