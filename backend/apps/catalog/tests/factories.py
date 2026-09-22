import factory
from factory.django import DjangoModelFactory

from apps.catalog.models import Course, DocumentType, GradingUnit, Scholarship, SchoolCycle, Section


class SchoolCycleFactory(DjangoModelFactory):
    class Meta:
        model = SchoolCycle

    year = factory.Sequence(lambda n: 2026 + n)
    start_date = "2026-01-12"
    end_date = "2026-10-30"
    status = SchoolCycle.ESTADO_ACTIVO


class GradingUnitFactory(DjangoModelFactory):
    class Meta:
        model = GradingUnit

    cycle = factory.SubFactory(SchoolCycleFactory)
    number = factory.Sequence(lambda n: (n % 4) + 1)
    start_date = "2026-01-12"
    end_date = "2026-02-28"
    grades_due_date = "2026-03-15"
    report_card_enabled_date = "2026-03-22"


class SectionFactory(DjangoModelFactory):
    class Meta:
        model = Section

    cycle = factory.SubFactory(SchoolCycleFactory)
    grade = "Segundo básico"
    letter = "A"
    type = Section.TIPO_ACADEMICA


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Curso de prueba {n}")
    type = Course.TIPO_ACADEMICO


class ScholarshipFactory(DjangoModelFactory):
    class Meta:
        model = Scholarship
        django_get_or_create = ("name",)

    name = "Beca completa"
    description = "Cubre el 100 % de la mensualidad."


class DocumentTypeFactory(DjangoModelFactory):
    class Meta:
        model = DocumentType
        django_get_or_create = ("name",)

    name = "Constancia de solvencia"
    template_key = "constancia_solvencia"
