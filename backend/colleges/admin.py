from django.contrib import admin

from .models import AcademicProgram, College, CollegeAdminProfile


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "email", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code", "email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(AcademicProgram)
class AcademicProgramAdmin(admin.ModelAdmin):
    list_display = ("college", "degree", "branch", "duration_years", "is_active")
    list_filter = ("college", "degree", "is_active")
    search_fields = ("college__name", "branch")


@admin.register(CollegeAdminProfile)
class CollegeAdminProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "college", "employee_id", "designation")
    list_filter = ("college", "designation")
    search_fields = ("user__email", "employee_id", "college__name")
    autocomplete_fields = ("user", "college")
    readonly_fields = ("created_at", "updated_at")

# Register your models here.
