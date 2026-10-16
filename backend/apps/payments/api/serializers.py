from rest_framework import serializers

from apps.students.models import Enrollment

from ..models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    enrollment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Enrollment.objects.all()
    )
    recorded_by = serializers.CharField(source="recorded_by.username", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "public_id",
            "enrollment",
            "concept",
            "period_month",
            "period_year",
            "amount",
            "payment_date",
            "receipt_number",
            "recorded_by",
        ]
        read_only_fields = ["public_id", "recorded_by", "amount", "receipt_number"]
        extra_kwargs = {"period_month": {"required": False}, "period_year": {"required": False}}
        # La unicidad (un pago por mes, una inscripción por ciclo) la valida
        # el servicio, con un mensaje en español.
        validators: list = []
