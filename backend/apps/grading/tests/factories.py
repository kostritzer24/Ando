import factory
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from apps.catalog.models import ActivityType
from apps.catalog.tests.factories import (
    CourseFactory,
    GradingUnitFactory,
    SchoolCycleFactory,
    SectionFactory,
)
from apps.scheduling.models import TeacherAssignment

from ..models import Activity


class ActivityTypeFactory(DjangoModelFactory):
    class Meta:
        model = ActivityType
        django_get_or_create = ("name",)

    name = "Prueba corta"
    counts_as_short_quiz = True


class TeacherAssignmentFactory(DjangoModelFactory):
    class Meta:
        model = TeacherAssignment

    teacher = factory.SubFactory(UserFactory)
    course = factory.SubFactory(CourseFactory)
    cycle = factory.SubFactory(SchoolCycleFactory)
    section = factory.SubFactory(SectionFactory, cycle=factory.SelfAttribute("..cycle"))


class ActivityFactory(DjangoModelFactory):
    class Meta:
        model = Activity

    assignment = factory.SubFactory(TeacherAssignmentFactory)
    unit = factory.SubFactory(GradingUnitFactory, cycle=factory.SelfAttribute("..assignment.cycle"))
    activity_type = factory.SubFactory(ActivityTypeFactory)
    name = "Prueba corta 1"
    max_score = 10
    due_date = "2026-02-01"
