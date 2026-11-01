from django.contrib import admin

from .models import Opportunity, OpportunityBookmark, OpportunityCollegeInvitation


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = (
        "title", "company", "opportunity_type", "status", "work_mode",
        "application_deadline", "openings",
    )
    list_filter = ("status", "opportunity_type", "work_mode", "target_colleges")
    search_fields = ("title", "company__name", "location", "required_skills__name")
    autocomplete_fields = (
        "company", "created_by", "target_colleges", "eligible_programs", "required_skills",
    )
    readonly_fields = ("published_at", "created_at", "updated_at")


@admin.register(OpportunityBookmark)
class OpportunityBookmarkAdmin(admin.ModelAdmin):
    list_display = ("student", "opportunity", "created_at")
    search_fields = ("student__user__email", "opportunity__title", "opportunity__company__name")
    readonly_fields = ("created_at",)


@admin.register(OpportunityCollegeInvitation)
class OpportunityCollegeInvitationAdmin(admin.ModelAdmin):
    list_display = ("opportunity", "college", "status", "submitted_by", "submitted_at", "reviewed_at")
    list_filter = ("status", "college")
    search_fields = ("opportunity__title", "opportunity__company__name", "college__name")
    filter_horizontal = ("eligible_programs",)
    readonly_fields = ("submitted_at", "reviewed_at", "updated_at")
