import factory
from factory.django import DjangoModelFactory

from apps.catalog.models import SchoolCycle, Section


class SchoolCycleFactory(DjangoModelFactory):
    class Meta:
        model = SchoolCycle

    year = factory.Sequence(lambda n: 2026 + n)
    start_date = "2026-01-12"
    end_date = "2026-10-30"
    status = SchoolCycle.ESTADO_ACTIVO


class SectionFactory(DjangoModelFactory):
    class Meta:
        model = Section

    cycle = factory.SubFactory(SchoolCycleFactory)
    grade = "Segundo básico"
    letter = "A"
    type = Section.TIPO_ACADEMICA
