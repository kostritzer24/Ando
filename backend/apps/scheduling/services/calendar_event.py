from datetime import date, time

from ..domain.calendar_event import validar_creacion
from ..models import CalendarEvent, Section, TeacherAssignment

ROL_DIRECCION = "Dirección"


def crear_evento(
    *,
    title: str,
    type: str,
    event_date: date,
    start_time: time,
    end_time: time,
    published_by,
    section: Section | None = None,
    assignment: TeacherAssignment | None = None,
    materials: str = "",
) -> CalendarEvent:
    """RF-22 / RN-17."""
    validar_creacion(
        event_type=type,
        tipo_institucional=CalendarEvent.TIPO_INSTITUCIONAL,
        is_direccion=published_by.role.name == ROL_DIRECCION,
        assignment=assignment,
        published_by=published_by,
    )
    return CalendarEvent.objects.create(
        title=title,
        type=type,
        event_date=event_date,
        start_time=start_time,
        end_time=end_time,
        section=section,
        assignment=assignment,
        materials=materials,
        published_by=published_by,
    )
