from datetime import timedelta

from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from accounts.permissions import IsCollegeAdmin, IsStudent
from accounts.services import send_activation_email

from .models import (
    StudentCertification,
    StudentExperience,
    StudentImportBatch,
    StudentProfile,
    StudentProject,
    StudentResume,
    StudentSkill,
)
from .serializers import (
    AdminStudentProfileSerializer,
    ProfileCompletionSerializer,
    StudentCertificationSerializer,
    StudentExperienceSerializer,
    StudentImportBatchSerializer,
    StudentImportUploadSerializer,
    StudentProfileSerializer,
    StudentProjectSerializer,
    StudentResumeSerializer,
    StudentSkillSerializer,
)
from .services import calculate_profile_completion
from .imports import build_template, confirm_import, preview_import


class OwnStudentProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentProfileSerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_object(self):
        return get_object_or_404(
            StudentProfile.objects.select_related("user", "college", "program"),
            user=self.request.user,
        )


class CollegeStudentListView(generics.ListAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = AdminStudentProfileSerializer
    queryset = StudentProfile.objects.none()
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "enrollment_number",
        "program__branch",
    )
    ordering_fields = ("user__first_name", "enrollment_number", "graduation_year")
    filterset_fields = ("user__is_active", "graduation_year", "program")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        queryset = StudentProfile.objects.select_related("user", "college", "program")
        admin_profile = getattr(self.request.user, "college_admin_profile", None)
        if self.request.user.is_superuser and admin_profile is None:
            return queryset
        if admin_profile is None:
            return queryset.none()
        return queryset.filter(college=admin_profile.college)


class CollegeStudentDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = AdminStudentProfileSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudentProfile.objects.none()
        admin_profile = getattr(self.request.user, "college_admin_profile", None)
        if admin_profile is None:
            return StudentProfile.objects.none()
        return StudentProfile.objects.select_related("user", "college", "program").filter(
            college=admin_profile.college,
        )


class CollegeStudentActivationResendView(generics.GenericAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = AdminStudentProfileSerializer

    def post(self, request, pk):
        student = get_object_or_404(
            StudentProfile.objects.select_related("user", "college", "program"),
            pk=pk,
            college=request.user.college_admin_profile.college,
        )
        user = student.user
        if user.activated_at or user.has_usable_password():
            raise ValidationError({"student": "This student has already activated their account."})
        if user.activation_email_sent_at and user.activation_email_sent_at > timezone.now() - timedelta(minutes=5):
            raise ValidationError({"student": "Wait five minutes before sending another activation email."})
        send_activation_email(user, student.college.name)
        return Response(self.get_serializer(student).data)


class CollegeStudentImportTemplateView(generics.GenericAPIView):
    permission_classes = (IsCollegeAdmin,)

    @extend_schema(responses={(200, "text/csv"): OpenApiTypes.BINARY})
    def get(self, request):
        college = request.user.college_admin_profile.college
        response = HttpResponse(build_template(college), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{college.code.lower()}-student-import.csv"'
        return response


class CollegeStudentImportListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = StudentImportBatchSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudentImportBatch.objects.none()
        return StudentImportBatch.objects.select_related("created_by", "college").filter(
            college=self.request.user.college_admin_profile.college,
        )[:20]

    @extend_schema(request=StudentImportUploadSerializer, responses={201: StudentImportBatchSerializer})
    def create(self, request, *args, **kwargs):
        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError({"file": "Choose a CSV file."})
        batch = preview_import(
            upload,
            request.user.college_admin_profile.college,
            request.user,
        )
        return Response(self.get_serializer(batch).data, status=status.HTTP_201_CREATED)


class CollegeStudentImportConfirmView(generics.GenericAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = StudentImportBatchSerializer

    @extend_schema(request=None, responses={200: StudentImportBatchSerializer})
    def post(self, request, pk):
        batch = get_object_or_404(
            StudentImportBatch.objects.select_related("college", "created_by"),
            pk=pk,
            college=request.user.college_admin_profile.college,
        )
        confirm_import(batch)
        return Response(self.get_serializer(batch).data)


class StudentOwnedListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsStudent,)
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        return self.queryset.filter(student__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(student=self.request.user.student_profile)


class StudentOwnedDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsStudent,)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        return self.queryset.filter(student__user=self.request.user)


class StudentSkillListCreateView(StudentOwnedListCreateView):
    serializer_class = StudentSkillSerializer
    queryset = StudentSkill.objects.select_related("skill", "student")


class StudentSkillDetailView(StudentOwnedDetailView):
    serializer_class = StudentSkillSerializer
    queryset = StudentSkill.objects.select_related("skill", "student")


class StudentProjectListCreateView(StudentOwnedListCreateView):
    serializer_class = StudentProjectSerializer
    queryset = StudentProject.objects.select_related("student")


class StudentProjectDetailView(StudentOwnedDetailView):
    serializer_class = StudentProjectSerializer
    queryset = StudentProject.objects.select_related("student")


class StudentCertificationListCreateView(StudentOwnedListCreateView):
    serializer_class = StudentCertificationSerializer
    queryset = StudentCertification.objects.select_related("student")


class StudentCertificationDetailView(StudentOwnedDetailView):
    serializer_class = StudentCertificationSerializer
    queryset = StudentCertification.objects.select_related("student")


class StudentExperienceListCreateView(StudentOwnedListCreateView):
    serializer_class = StudentExperienceSerializer
    queryset = StudentExperience.objects.select_related("student")


class StudentExperienceDetailView(StudentOwnedDetailView):
    serializer_class = StudentExperienceSerializer
    queryset = StudentExperience.objects.select_related("student")


class StudentResumeListCreateView(StudentOwnedListCreateView):
    serializer_class = StudentResumeSerializer
    queryset = StudentResume.objects.select_related("student", "student__user")
    parser_classes = (MultiPartParser, FormParser)


class StudentResumeDetailView(StudentOwnedDetailView):
    serializer_class = StudentResumeSerializer
    queryset = StudentResume.objects.select_related("student", "student__user")
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def perform_destroy(self, instance):
        student = instance.student
        was_primary = instance.is_primary
        try:
            instance.delete()
        except ProtectedError as error:
            raise ValidationError(
                "This resume is attached to an application and must be kept as an application record."
            ) from error
        if was_primary:
            replacement = StudentResume.objects.filter(student=student).order_by("-updated_at").first()
            if replacement:
                replacement.is_primary = True
                replacement.save(update_fields=("is_primary", "updated_at"))


class StudentProfileCompletionView(generics.GenericAPIView):
    permission_classes = (IsStudent,)
    serializer_class = ProfileCompletionSerializer

    def get(self, request):
        return Response(calculate_profile_completion(request.user.student_profile))
