from rest_framework import serializers

from apps.catalog.models import DocumentType
from apps.students.models import Enrollment

from ..models import IssuedDocument


class IssuedDocumentSerializer(serializers.ModelSerializer):
    document_type = serializers.SlugRelatedField(slug_field="name", read_only=True)
    enrollment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Enrollment.objects.all()
    )
    issued_by = serializers.CharField(source="issued_by.username", read_only=True)

    class Meta:
        model = IssuedDocument
        fields = [
            "public_id",
            "document_type",
            "enrollment",
            "verification_code",
            "issued_at",
            "issued_by",
        ]
        read_only_fields = fields


class DocumentIssueSerializer(serializers.Serializer):
    enrollment = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Enrollment.objects.all()
    )
    document_type = serializers.SlugRelatedField(
        slug_field="public_id", queryset=DocumentType.objects.all()
    )
    custom_text = serializers.CharField(required=False, allow_blank=True, default="")
