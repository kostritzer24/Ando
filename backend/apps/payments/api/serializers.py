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
            "period_month",
            "period_year",
            "amount",
            "payment_date",
            "receipt_number",
            "recorded_by",
        ]
        read_only_fields = ["public_id", "recorded_by"]
