from rest_framework import serializers

from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id", "category", "category_display", "title", "message",
            "link", "is_read", "read_at", "created_at",
        )


class NotificationUnreadCountSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField(read_only=True)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = (
            "email_enabled", "email_company", "email_applications", "email_interviews",
            "email_placements", "email_announcements", "email_system", "updated_at",
        )
        read_only_fields = ("updated_at",)
