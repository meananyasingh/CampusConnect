from django.contrib import admin

from .models import Company, CompanyCollegePartnership, RecruiterProfile


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "contact_email", "is_active", "created_at")
    list_filter = ("is_active", "industry")
    search_fields = ("name", "contact_email", "website")
    readonly_fields = ("slug", "created_at", "updated_at")


@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "designation", "is_company_owner")
    list_filter = ("is_company_owner", "company")
    search_fields = ("user__email", "user__first_name", "user__last_name", "company__name")
    autocomplete_fields = ("user", "company")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CompanyCollegePartnership)
class CompanyCollegePartnershipAdmin(admin.ModelAdmin):
    list_display = ("company", "college", "status", "reviewed_by", "reviewed_at")
    list_filter = ("status", "college")
    search_fields = ("company__name", "college__name")
    autocomplete_fields = ("company", "college", "reviewed_by")
    readonly_fields = ("created_at", "updated_at")
