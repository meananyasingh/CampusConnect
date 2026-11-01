from django.contrib import admin

from .models import Announcement, AnnouncementRead


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "college", "company", "announcement_type", "priority", "approval_status", "publish_at")
    list_filter = ("approval_status", "announcement_type", "priority", "is_pinned", "is_archived", "college")
    search_fields = ("title", "body", "college__name", "company__name")
    filter_horizontal = ("target_programs",)
    readonly_fields = ("created_at", "updated_at", "reviewed_at")


@admin.register(AnnouncementRead)
class AnnouncementReadAdmin(admin.ModelAdmin):
    list_display = ("announcement", "user", "read_at")
    search_fields = ("announcement__title", "user__email")
    readonly_fields = ("read_at",)
