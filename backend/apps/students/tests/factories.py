import factory
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from apps.catalog.tests.factories import SchoolCycleFactory, SectionFactory

from ..models import Enrollment, Guardian, Student


class StudentFactory(DjangoModelFactory):
    class Meta:
        model = Student

    internal_code = factory.Sequence(lambda n: f"ES{n + 1:03d}")
    first_name = "María Ximena"
    last_name = "Pérez Tzul"
    birth_date = "2013-05-14"


class GuardianFactory(DjangoModelFactory):
    class Meta:
        model = Guardian

    # El rol del usuario no se fija acá a propósito: las pruebas que
    # necesitan el rol exacto "Padre de familia" (para ejercer el alcance
    # por objeto) lo pasan explícito al crear el usuario.
    user = factory.SubFactory(UserFactory)
    full_name = "Encargada de prueba"


class EnrollmentFactory(DjangoModelFactory):
    class Meta:
        model = Enrollment

    student = factory.SubFactory(StudentFactory)
    section = factory.SubFactory(SectionFactory)
    cycle = factory.SubFactory(SchoolCycleFactory)
    enrolled_at = "2026-01-12"
