from pathlib import Path

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from notifications.models import Notification
from notifications.services import create_notification, notify_college_admins

from .models import StudentDocument
from .services import document_verification_summary


class StudentDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source="get_document_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentDocument
        fields = (
            "id", "document_type", "document_type_display", "title", "academic_year",
            "file", "original_filename", "file_size", "student_note", "status",
            "status_display", "review_note", "reviewed_by_name", "reviewed_at",
            "created_at", "updated_at",
        )
        extra_kwargs = {"file": {"write_only": True}}
        read_only_fields = (
            "id", "original_filename", "file_size", "status", "status_display",
            "review_note", "reviewed_by_name", "reviewed_at", "created_at", "updated_at",
        )

    def get_reviewed_by_name(self, instance) -> str:
        if not instance.reviewed_by:
            return ""
        return instance.reviewed_by.get_full_name() or instance.reviewed_by.email

    def validate_file(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Document must not exceed 5 MB.")
        extension = Path(value.name).suffix.lower()
        if extension not in {".pdf", ".jpg", ".jpeg", ".png"}:
            raise serializers.ValidationError("Upload a PDF, JPEG, or PNG document.")
        signature = value.read(16)
        value.seek(0)
        valid_signature = (
            (extension == ".pdf" and signature.startswith(b"%PDF-"))
            or (extension in {".jpg", ".jpeg"} and signature.startswith(b"\xff\xd8\xff"))
            or (extension == ".png" and signature.startswith(b"\x89PNG\r\n\x1a\n"))
        )
        if not valid_signature:
            raise serializers.ValidationError("The file content does not match its extension.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        student = self.context["request"].user.student_profile
        document_type = attrs.get("document_type")
        if StudentDocument.objects.filter(
            student=student,
            document_type=document_type,
            status=StudentDocument.Status.PENDING,
        ).exists():
            raise serializers.ValidationError(
                {"document_type": "This document type already has a submission awaiting review."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        student = self.context["request"].user.student_profile
        uploaded_file = validated_data["file"]
        validated_data["original_filename"] = Path(uploaded_file.name).name
        validated_data["file_size"] = uploaded_file.size
        try:
            document = StudentDocument.objects.create(student=student, **validated_data)
        except IntegrityError as error:
            raise serializers.ValidationError(
                {"document_type": "This document type already has a submission awaiting review."}
            ) from error
        notify_college_admins(
            college=student.college,
            category=Notification.Category.SYSTEM,
            title="Student document awaiting verification",
            message=f"{student.user.get_full_name() or student.user.email} submitted {document.get_document_type_display()}.",
            link="/admin/documents",
        )
        return document


class AdminDocumentStudentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email")
    enrollment_number = serializers.CharField()
    program = serializers.CharField(source="program.branch")
    graduation_year = serializers.IntegerField()

    def get_name(self, instance) -> str:
        return instance.user.get_full_name() or instance.user.email


class AdminStudentDocumentSerializer(StudentDocumentSerializer):
    student = AdminDocumentStudentSerializer(read_only=True)

    class Meta(StudentDocumentSerializer.Meta):
        fields = StudentDocumentSerializer.Meta.fields + ("student",)
        read_only_fields = StudentDocumentSerializer.Meta.read_only_fields + (
            "document_type", "title", "academic_year", "student_note", "student",
        )


class StudentDocumentReviewSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=(
        StudentDocument.Status.VERIFIED,
        StudentDocument.Status.REJECTED,
    ))

    class Meta:
        model = StudentDocument
        fields = ("status", "review_note")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance.status != StudentDocument.Status.PENDING:
            raise serializers.ValidationError("Only a pending document can be reviewed.")
        if "status" not in attrs:
            raise serializers.ValidationError({"status": "Choose verify or reject."})
        if attrs["status"] == StudentDocument.Status.REJECTED and not attrs.get(
            "review_note", ""
        ).strip():
            raise serializers.ValidationError({"review_note": "Explain why the document is rejected."})
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.review_note = validated_data.get("review_note", "")
        instance.reviewed_by = self.context["request"].user
        instance.reviewed_at = timezone.now()
        instance.save(update_fields=(
            "status", "review_note", "reviewed_by", "reviewed_at", "updated_at",
        ))
        create_notification(
            recipient=instance.student.user,
            category=Notification.Category.SYSTEM,
            title=f"Document {instance.get_status_display().lower()}",
            message=f"Your {instance.get_document_type_display()} was {instance.get_status_display().lower()}.",
            link="/student/documents",
        )
        return instance


class DocumentVerificationSummarySerializer(serializers.Serializer):
    is_complete = serializers.BooleanField()
    verified_required = serializers.IntegerField()
    required_total = serializers.IntegerField()
    percentage = serializers.IntegerField()
    requirements = serializers.ListField(child=serializers.DictField())

    @staticmethod
    def for_student(student):
        return document_verification_summary(student)

