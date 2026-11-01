from pathlib import Path

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from accounts.permissions import IsCollegeAdmin, IsStudent

from .models import StudentDocument
from .serializers import (
    AdminStudentDocumentSerializer,
    DocumentVerificationSummarySerializer,
    StudentDocumentReviewSerializer,
    StudentDocumentSerializer,
)
from .services import document_verification_summary


document_queryset = StudentDocument.objects.select_related(
    "student", "student__user", "student__college", "student__program", "reviewed_by",
)


class StudentDocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentDocumentSerializer
    parser_classes = (MultiPartParser, FormParser)
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return document_queryset.none()
        return document_queryset.filter(student__user=self.request.user)


class StudentDocumentDetailView(generics.DestroyAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentDocumentSerializer

    def get_queryset(self):
        return document_queryset.filter(student__user=self.request.user)

    def perform_destroy(self, instance):
        if instance.status == StudentDocument.Status.VERIFIED:
            raise ValidationError("A verified document is part of your placement record and cannot be deleted.")
        instance.delete()


class StudentDocumentDownloadView(generics.GenericAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentDocumentSerializer

    def get(self, request, pk):
        document = get_object_or_404(document_queryset, pk=pk, student__user=request.user)
        return document_file_response(document)


class StudentDocumentSummaryView(generics.GenericAPIView):
    permission_classes = (IsStudent,)
    serializer_class = DocumentVerificationSummarySerializer

    def get(self, request):
        return Response(document_verification_summary(request.user.student_profile))


class AdminStudentDocumentListView(generics.ListAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = AdminStudentDocumentSerializer
    queryset = StudentDocument.objects.none()
    filterset_fields = ("status", "document_type", "student__program", "student__graduation_year")
    search_fields = (
        "student__user__first_name", "student__user__last_name", "student__user__email",
        "student__enrollment_number", "title", "original_filename",
    )
    ordering_fields = ("created_at", "reviewed_at", "student__user__first_name")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        admin_profile = getattr(self.request.user, "college_admin_profile", None)
        if self.request.user.is_superuser and admin_profile is None:
            return document_queryset
        if admin_profile is None:
            return document_queryset.none()
        return document_queryset.filter(student__college=admin_profile.college)


class AdminStudentDocumentReviewView(generics.GenericAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = StudentDocumentReviewSerializer

    def get_queryset(self):
        admin_profile = getattr(self.request.user, "college_admin_profile", None)
        if self.request.user.is_superuser and admin_profile is None:
            return document_queryset
        if admin_profile is None:
            return document_queryset.none()
        return document_queryset.filter(student__college=admin_profile.college)

    def patch(self, request, pk):
        document = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        return Response(AdminStudentDocumentSerializer(document).data)


class AdminStudentDocumentDownloadView(AdminStudentDocumentReviewView):
    serializer_class = AdminStudentDocumentSerializer
    http_method_names = ("get", "head", "options")

    def get(self, request, pk):
        document = get_object_or_404(self.get_queryset(), pk=pk)
        return document_file_response(document)


def document_file_response(document):
    content_types = {".pdf": "application/pdf", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
    content_type = content_types.get(Path(document.file.name).suffix.lower(), "application/octet-stream")
    return FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=document.original_filename,
        content_type=content_type,
    )
