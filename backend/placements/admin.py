from django.contrib import admin

from .models import CollegePlacementPolicy, PlacementDrive, PlacementRecord


@admin.register(CollegePlacementPolicy)
class CollegePlacementPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "college", "applications_enabled", "require_verified_documents",
        "minimum_profile_completion", "minimum_cgpa", "max_active_backlogs", "updated_at",
    )
    list_filter = ("applications_enabled", "require_verified_documents")
    search_fields = ("college__name", "college__code")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PlacementDrive)
class PlacementDriveAdmin(admin.ModelAdmin):
    list_display = ("title", "college", "start_date", "end_date", "status")
    list_filter = ("status", "college")
    search_fields = ("title", "college__name", "venue")
    filter_horizontal = ("opportunities",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(PlacementRecord)
class PlacementRecordAdmin(admin.ModelAdmin):
    list_display = ("application", "college", "annual_package", "status", "offer_date")
    list_filter = ("status", "college", "application__opportunity__company")
    search_fields = (
        "application__student__user__email", "application__student__user__first_name",
        "application__student__user__last_name", "application__opportunity__company__name",
    )
    autocomplete_fields = ("application", "college", "verified_by")
    readonly_fields = ("created_at", "updated_at")
