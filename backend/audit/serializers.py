from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = AuditEvent
        fields = (
            "id", "actor_email", "actor_name", "actor_role", "category",
            "category_display", "action", "description", "http_method", "target_type",
            "target_id", "target_label", "changed_fields", "context", "ip_address", "created_at",
        )
        read_only_fields = fields
