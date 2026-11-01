from django.db.models import Avg, Max
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from accounts.permissions import IsCollegeAdmin, IsRecruiter, IsStudent
from applications.models import Application, InterviewSchedule
from applications.serializers import ApplicationSerializer, InterviewScheduleSerializer
from companies.models import CompanyCollegePartnership, RecruiterProfile
from opportunities.models import Opportunity
from opportunities.serializers import OpportunitySerializer
from students.models import StudentProfile

from .models import CollegePlacementPolicy, PlacementDrive, PlacementRecord
from .serializers import (
    CollegeDashboardSerializer,
    CollegePlacementPolicySerializer,
    PlacementDriveSerializer,
    PlacementRecordSerializer,
    StudentPlacementDecisionSerializer,
    StudentPlacementRecordSerializer,
    StudentPlacementReadinessSerializer,
)
from .services import get_student_placement_readiness


drive_queryset = PlacementDrive.objects.select_related("college", "created_by").prefetch_related(
    "opportunities", "opportunities__company",
)


placement_queryset = PlacementRecord.objects.select_related(
    "college", "verified_by", "application", "application__opportunity",
    "application__opportunity__company", "application__student", "application__student__user",
    "application__student__college", "application__student__program", "application__resume",
).prefetch_related("application__status_history", "application__status_history__changed_by")


def get_admin_college(user):
    profile = getattr(user, "college_admin_profile", None)
    if profile is None:
        raise PermissionDenied("Configure a college admin profile before using placement management.")
    return profile.college


class CollegeDashboardView(generics.GenericAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = CollegeDashboardSerializer

    def get(self, request):
        college = get_admin_college(request.user)
        students = StudentProfile.objects.filter(college=college)
        applications = Application.objects.filter(student__college=college)
        verified_partnerships = CompanyCollegePartnership.objects.filter(
            college=college,
            status=CompanyCollegePartnership.Status.VERIFIED,
        )
        placements = PlacementRecord.objects.filter(college=college).exclude(
            status__in=(PlacementRecord.Status.DECLINED, PlacementRecord.Status.CANCELLED),
        )
        package_stats = placements.aggregate(
            average=Avg("annual_package"),
            highest=Max("annual_package"),
        )
        student_count = students.count()
        placed_count = placements.values("application__student").distinct().count()
        return Response({
            "college": {"id": college.id, "name": college.name, "code": college.code},
            "total_students": student_count,
            "total_recruiters": RecruiterProfile.objects.filter(
                company__college_partnerships__in=verified_partnerships,
            ).distinct().count(),
            "verified_companies": verified_partnerships.values("company").distinct().count(),
            "active_opportunities": Opportunity.objects.filter(
                target_colleges=college,
                status=Opportunity.Status.PUBLISHED,
                application_deadline__gte=timezone.localdate(),
            ).distinct().count(),
            "total_applications": applications.count(),
            "shortlisted_candidates": applications.filter(
                status__in=(Application.Status.SHORTLISTED, Application.Status.INTERVIEW),
            ).count(),
            "upcoming_interviews": InterviewSchedule.objects.filter(
                application__student__college=college,
                status=InterviewSchedule.Status.SCHEDULED,
                scheduled_at__gte=timezone.now(),
            ).count(),
            "placed_students": placed_count,
            "placement_percentage": round((placed_count / student_count * 100), 2) if student_count else 0,
            "average_package": package_stats["average"],
            "highest_package": package_stats["highest"],
        })


class CollegePlacementPolicyView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = CollegePlacementPolicySerializer

    def get_object(self):
        college = get_admin_college(self.request.user)
        policy, _ = CollegePlacementPolicy.objects.select_related(
            "college", "updated_by"
        ).get_or_create(college=college)
        return policy

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class StudentPlacementReadinessView(generics.GenericAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentPlacementReadinessSerializer

    def get(self, request):
        return Response(get_student_placement_readiness(request.user.student_profile))


class CollegeDriveOpportunityListView(generics.ListAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = OpportunitySerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Opportunity.objects.none()
        college = get_admin_college(self.request.user)
        return Opportunity.objects.select_related("company", "created_by").prefetch_related(
            "target_colleges", "eligible_programs", "required_skills",
        ).filter(
            target_colleges=college,
            company__college_partnerships__college=college,
            company__college_partnerships__status=CompanyCollegePartnership.Status.VERIFIED,
            status__in=(Opportunity.Status.PUBLISHED, Opportunity.Status.CLOSED),
        ).distinct()


class CollegePlacementDriveListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = PlacementDriveSerializer
    pagination_class = None
    filterset_fields = ("status",)
    search_fields = ("title", "venue", "opportunities__company__name")
    ordering_fields = ("start_date", "end_date", "created_at")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return drive_queryset.none()
        return drive_queryset.filter(college=get_admin_college(self.request.user)).distinct()


class CollegePlacementDriveDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = PlacementDriveSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return drive_queryset.none()
        return drive_queryset.filter(college=get_admin_college(self.request.user))

    def perform_destroy(self, instance):
        if instance.status != PlacementDrive.Status.DRAFT:
            raise PermissionDenied("Only a draft placement drive can be deleted.")
        instance.delete()


class StudentPlacementDriveListView(generics.ListAPIView):
    permission_classes = (IsStudent,)
    serializer_class = PlacementDriveSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return drive_queryset.none()
        return drive_queryset.filter(
            college=self.request.user.student_profile.college,
            status__in=(
                PlacementDrive.Status.UPCOMING,
                PlacementDrive.Status.ONGOING,
                PlacementDrive.Status.COMPLETED,
            ),
        )


class RecruiterPlacementDriveListView(generics.ListAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = PlacementDriveSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return drive_queryset.none()
        return drive_queryset.filter(
            opportunities__company=self.request.user.recruiter_profile.company,
        ).exclude(status=PlacementDrive.Status.DRAFT).distinct()


class CollegeApplicationListView(generics.ListAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = ApplicationSerializer
    filterset_fields = ("status", "opportunity", "opportunity__company")
    search_fields = (
        "student__user__first_name", "student__user__last_name", "student__user__email",
        "student__enrollment_number", "opportunity__title", "opportunity__company__name",
    )
    ordering_fields = ("applied_at", "updated_at", "student__cgpa")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Application.objects.none()
        college = get_admin_college(self.request.user)
        return Application.objects.select_related(
            "opportunity", "opportunity__company", "student", "student__user",
            "student__college", "student__program", "resume",
        ).prefetch_related("status_history", "status_history__changed_by").filter(student__college=college)


class CollegeInterviewListView(generics.ListAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = InterviewScheduleSerializer
    filterset_fields = ("status", "result", "application__opportunity")
    ordering_fields = ("scheduled_at",)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return InterviewSchedule.objects.none()
        college = get_admin_college(self.request.user)
        return InterviewSchedule.objects.select_related(
            "recruitment_round", "recruitment_round__opportunity", "recruitment_round__opportunity__company",
            "application", "application__opportunity", "application__opportunity__company",
            "application__student", "application__student__user", "application__student__college",
            "application__student__program", "application__resume", "created_by",
        ).prefetch_related("application__status_history", "application__status_history__changed_by").filter(
            application__student__college=college,
        )


class CollegePlacementListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = PlacementRecordSerializer
    filterset_fields = ("status", "application__opportunity__company")
    search_fields = (
        "application__student__user__first_name", "application__student__user__last_name",
        "application__student__enrollment_number", "application__opportunity__company__name",
    )

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return placement_queryset.none()
        return placement_queryset.filter(college=get_admin_college(self.request.user))


class CollegePlacementDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = PlacementRecordSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return placement_queryset.none()
        return placement_queryset.filter(college=get_admin_college(self.request.user))


class StudentPlacementListView(generics.ListAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentPlacementRecordSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return placement_queryset.none()
        return placement_queryset.filter(application__student__user=self.request.user)


class StudentPlacementDecisionView(generics.GenericAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentPlacementDecisionSerializer

    def patch(self, request, *args, **kwargs):
        placement = get_object_or_404(
            placement_queryset.filter(application__student__user=request.user),
            pk=self.kwargs["pk"],
        )
        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "placement": placement},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(StudentPlacementRecordSerializer(placement, context={"request": request}).data)
