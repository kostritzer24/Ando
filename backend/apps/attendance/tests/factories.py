import factory
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from apps.students.tests.factories import EnrollmentFactory

from ..models import Attendance


class AttendanceFactory(DjangoModelFactory):
    class Meta:
        model = Attendance

    enrollment = factory.SubFactory(EnrollmentFactory)
    date = "2026-01-13"
    status = Attendance.ESTADO_PRESENTE
    recorded_by = factory.SubFactory(UserFactory)
