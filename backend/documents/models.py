from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def student_document_upload_path(instance, filename):
    return f"students/documents/{instance.student.user_id}/{filename}"


class StudentDocument(models.Model):
    class DocumentType(models.TextChoices):
        TENTH_MARKSHEET = "TENTH_MARKSHEET", "10th marksheet"
        TWELFTH_MARKSHEET = "TWELFTH_MARKSHEET", "12th marksheet"
        DIPLOMA_MARKSHEET = "DIPLOMA_MARKSHEET", "Diploma marksheet"
        COLLEGE_ID = "COLLEGE_ID", "College identity card"
        CURRENT_TRANSCRIPT = "CURRENT_TRANSCRIPT", "Current academic transcript"
        DEGREE_CERTIFICATE = "DEGREE_CERTIFICATE", "Degree or provisional certificate"
        OTHER = "OTHER", "Other placement document"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Awaiting verification"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    title = models.CharField(max_length=150)
    academic_year = models.CharField(max_length=20, blank=True)
    file = models.FileField(upload_to=student_document_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    student_note = models.TextField(max_length=500, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    review_note = models.TextField(max_length=1000, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_student_documents",
        blank=True,
        null=True,
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("student", "document_type"),
                condition=Q(status="PENDING"),
                name="one_pending_document_per_student_type",
            )
        ]

    def clean(self):
        if self.reviewed_by_id:
            admin_profile = getattr(self.reviewed_by, "college_admin_profile", None)
            if self.reviewed_by.role != "ADMIN" or (
                admin_profile and admin_profile.college_id != self.student.college_id
            ):
                raise ValidationError({"reviewed_by": "The reviewer must administer the student's college."})

    def save(self, *args, **kwargs):
        self.title = " ".join(self.title.split())
        if self.file:
            self.original_filename = self.original_filename or Path(self.file.name).name
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        storage = self.file.storage
        file_name = self.file.name
        result = super().delete(*args, **kwargs)
        if file_name:
            storage.delete(file_name)
        return result

    def __str__(self):
        return f"{self.student.user.email} - {self.get_document_type_display()}"

