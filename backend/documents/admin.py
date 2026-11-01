from django.contrib import admin

from .models import StudentDocument


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ("student", "document_type", "title", "status", "created_at", "reviewed_at")
    list_filter = ("status", "document_type", "student__college")
    search_fields = ("student__user__email", "student__enrollment_number", "title")
    readonly_fields = ("original_filename", "file_size", "created_at", "updated_at", "reviewed_at")

