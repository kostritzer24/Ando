import factory
from factory.django import DjangoModelFactory

from apps.accounts.tests.factories import UserFactory
from apps.students.tests.factories import EnrollmentFactory

from ..models import Payment


class PaymentFactory(DjangoModelFactory):
    class Meta:
        model = Payment

    enrollment = factory.SubFactory(EnrollmentFactory)
    period_month = factory.Sequence(lambda n: (n % 12) + 1)
    period_year = 2026
    amount = "150.00"
    payment_date = "2026-02-05"
    receipt_number = factory.Sequence(lambda n: f"R-{n + 1:05d}")
    recorded_by = factory.SubFactory(UserFactory)
