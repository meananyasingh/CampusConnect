from django.contrib import admin

from .models import Application, ApplicationStatusHistory, InterviewSchedule, RecruitmentRound


class ApplicationStatusHistoryInline(admin.TabularInline):
    model = ApplicationStatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "note", "created_at")
    can_delete = False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("student", "opportunity", "status", "applied_at")
    list_filter = ("status", "opportunity__company", "opportunity")
    search_fields = (
        "student__user__email", "student__user__first_name",
        "student__user__last_name", "opportunity__title",
    )
    autocomplete_fields = ("opportunity", "student", "resume")
    readonly_fields = ("applied_at", "updated_at")
    inlines = (ApplicationStatusHistoryInline,)


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("application", "from_status", "to_status", "changed_by", "created_at")
    list_filter = ("to_status", "created_at")
    readonly_fields = ("created_at",)


@admin.register(RecruitmentRound)
class RecruitmentRoundAdmin(admin.ModelAdmin):
    list_display = ("name", "opportunity", "sequence", "round_type", "created_by")
    list_filter = ("round_type", "opportunity__company")
    search_fields = ("name", "opportunity__title", "opportunity__company__name")
    autocomplete_fields = ("opportunity", "created_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(InterviewSchedule)
class InterviewScheduleAdmin(admin.ModelAdmin):
    list_display = ("application", "recruitment_round", "scheduled_at", "status", "result")
    list_filter = ("status", "result", "mode", "recruitment_round__opportunity__company")
    search_fields = (
        "application__student__user__email", "application__student__user__first_name",
        "application__student__user__last_name", "recruitment_round__name",
    )
    autocomplete_fields = ("application", "recruitment_round", "created_by")
    readonly_fields = ("created_at", "updated_at")
