from django.contrib import admin

from .models import (
    Skill,
    StudentCertification,
    StudentExperience,
    StudentImportBatch,
    StudentProfile,
    StudentProject,
    StudentResume,
    StudentSkill,
)

admin.site.register(StudentImportBatch)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "enrollment_number",
        "college",
        "program",
        "graduation_year",
        "cgpa",
        "active_backlogs",
    )
    list_filter = ("college", "program", "graduation_year", "active_backlogs")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "enrollment_number",
    )
    autocomplete_fields = ("user", "college", "program")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(StudentSkill)
class StudentSkillAdmin(admin.ModelAdmin):
    list_display = ("student", "skill", "proficiency", "years_experience")
    list_filter = ("proficiency",)
    search_fields = ("student__user__email", "skill__name")
    autocomplete_fields = ("student", "skill")


@admin.register(StudentProject)
class StudentProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "start_date", "end_date", "is_ongoing")
    list_filter = ("is_ongoing",)
    search_fields = ("title", "student__user__email", "technologies")
    autocomplete_fields = ("student",)


@admin.register(StudentCertification)
class StudentCertificationAdmin(admin.ModelAdmin):
    list_display = ("name", "student", "issuing_organization", "issue_date", "expiry_date")
    search_fields = ("name", "issuing_organization", "student__user__email")
    autocomplete_fields = ("student",)


@admin.register(StudentExperience)
class StudentExperienceAdmin(admin.ModelAdmin):
    list_display = ("role", "organization", "student", "employment_type", "is_current")
    list_filter = ("employment_type", "is_current")
    search_fields = ("role", "organization", "student__user__email")
    autocomplete_fields = ("student",)


@admin.register(StudentResume)
class StudentResumeAdmin(admin.ModelAdmin):
    list_display = ("title", "student", "original_filename", "is_primary", "updated_at")
    list_filter = ("is_primary",)
    search_fields = ("title", "original_filename", "student__user__email")
    autocomplete_fields = ("student",)
    readonly_fields = ("original_filename", "file_size", "created_at", "updated_at")
