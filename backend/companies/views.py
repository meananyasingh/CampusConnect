from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from accounts.permissions import IsCollegeAdmin, IsRecruiter

from .models import Company, CompanyCollegePartnership, RecruiterProfile
from .serializers import (
    CompanySerializer,
    PartnershipAdminSerializer,
    RecruiterPartnershipSerializer,
    RecruiterProfileSerializer,
)


class OwnRecruiterProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = RecruiterProfileSerializer

    def get_object(self):
        return get_object_or_404(
            RecruiterProfile.objects.select_related("user", "company").prefetch_related(
                "company__college_partnerships__college"
            ),
            user=self.request.user,
        )


class OwnCompanyView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = CompanySerializer
    parser_classes = (JSONParser, MultiPartParser, FormParser)

    def get_object(self):
        profile = get_object_or_404(RecruiterProfile, user=self.request.user)
        return Company.objects.prefetch_related("college_partnerships__college").get(pk=profile.company_id)

    def perform_update(self, serializer):
        if not self.request.user.recruiter_profile.is_company_owner:
            raise PermissionDenied("Only the company owner can update the company profile.")
        serializer.save()


class RecruiterPartnershipListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = RecruiterPartnershipSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CompanyCollegePartnership.objects.none()
        return CompanyCollegePartnership.objects.select_related("college").filter(
            company=self.request.user.recruiter_profile.company
        )

    def perform_create(self, serializer):
        serializer.save(company=self.request.user.recruiter_profile.company)


class RecruiterPartnershipDetailView(generics.DestroyAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = RecruiterPartnershipSerializer

    def get_queryset(self):
        return CompanyCollegePartnership.objects.filter(
            company=self.request.user.recruiter_profile.company
        )

    def perform_destroy(self, instance):
        if instance.status != CompanyCollegePartnership.Status.PENDING:
            raise ValidationError("Only a pending college request can be cancelled.")
        instance.delete()


class CollegeCompanyPartnershipListView(generics.ListAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = PartnershipAdminSerializer
    queryset = CompanyCollegePartnership.objects.none()
    search_fields = ("company__name", "company__industry", "company__contact_email")
    ordering_fields = ("created_at", "updated_at", "company__name", "status")
    filterset_fields = ("status",)

    def get_queryset(self):
        queryset = CompanyCollegePartnership.objects.select_related("company", "college")
        admin_profile = getattr(self.request.user, "college_admin_profile", None)
        if self.request.user.is_superuser and admin_profile is None:
            return queryset
        if admin_profile is None:
            return queryset.none()
        return queryset.filter(college=admin_profile.college)


class CollegeCompanyPartnershipDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = PartnershipAdminSerializer

    def get_queryset(self):
        queryset = CompanyCollegePartnership.objects.select_related("company", "college")
        admin_profile = getattr(self.request.user, "college_admin_profile", None)
        if self.request.user.is_superuser and admin_profile is None:
            return queryset
        if admin_profile is None:
            return queryset.none()
        return queryset.filter(college=admin_profile.college)
