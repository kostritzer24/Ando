import factory
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import CourseFactory, SchoolCycleFactory, SectionFactory

from ..models import TeacherAssignment


class TeacherAssignmentFactory(DjangoModelFactory):
    class Meta:
        model = TeacherAssignment

    teacher = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    cycle = factory.SubFactory(SchoolCycleFactory)
    section = factory.SubFactory(SectionFactory, cycle=factory.SelfAttribute("..cycle"))
