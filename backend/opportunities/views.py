from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsCollegeAdmin, IsRecruiter, IsStudent

from .filters import StudentOpportunityFilter
from .models import Opportunity, OpportunityBookmark, OpportunityCollegeInvitation
from .serializers import (
    CollegeOpportunityInvitationSerializer,
    CollegeOpportunityReviewSerializer,
    OpportunityBookmarkStateSerializer,
    OpportunityCollegeShareSerializer,
    OpportunitySerializer,
    RecommendedOpportunitySerializer,
    StudentOpportunitySerializer,
)
from .services import get_recommended_opportunities


opportunity_queryset = Opportunity.objects.select_related("company", "created_by").prefetch_related(
    "target_colleges", "eligible_programs", "required_skills", "bookmarks",
    "college_invitations__college", "college_invitations__eligible_programs",
    "college_invitations__reviewed_by",
)


def student_opportunity_queryset(user):
    college = user.student_profile.college
    return opportunity_queryset.filter(
        status=Opportunity.Status.PUBLISHED,
        application_deadline__gte=timezone.localdate(),
        company__is_active=True,
        target_colleges=college,
        company__college_partnerships__college=college,
        company__college_partnerships__status="VERIFIED",
    ).distinct()


class RecruiterOpportunityListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = OpportunitySerializer
    search_fields = ("title", "location", "description")
    filterset_fields = ("status", "opportunity_type", "work_mode")
    ordering_fields = ("created_at", "application_deadline", "title")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return opportunity_queryset.none()
        return opportunity_queryset.filter(company=self.request.user.recruiter_profile.company)

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.recruiter_profile.company,
            created_by=self.request.user,
        )


class RecruiterOpportunityDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = OpportunitySerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return opportunity_queryset.none()
        return opportunity_queryset.filter(company=self.request.user.recruiter_profile.company)

    def perform_destroy(self, instance):
        if instance.status != Opportunity.Status.DRAFT:
            raise ValidationError("Only draft opportunities can be deleted. Close or cancel published opportunities.")
        if instance.college_invitations.exclude(
            status=OpportunityCollegeInvitation.Status.WITHDRAWN
        ).exists():
            raise ValidationError("Withdraw active college invitations before deleting this draft.")
        instance.delete()


class RecruiterOpportunityCollegeShareView(generics.GenericAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = OpportunityCollegeShareSerializer

    def get_opportunity(self):
        return get_object_or_404(
            opportunity_queryset.filter(company=self.request.user.recruiter_profile.company),
            pk=self.kwargs["pk"],
        )

    def post(self, request, *args, **kwargs):
        opportunity = self.get_opportunity()
        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "opportunity": opportunity},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        refreshed = opportunity_queryset.get(pk=opportunity.pk)
        return Response(OpportunitySerializer(refreshed, context={"request": request}).data)


class RecruiterOpportunityInvitationDetailView(generics.DestroyAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = CollegeOpportunityInvitationSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return OpportunityCollegeInvitation.objects.none()
        return OpportunityCollegeInvitation.objects.filter(
            opportunity__company=self.request.user.recruiter_profile.company,
        )

    def perform_destroy(self, instance):
        if instance.status != OpportunityCollegeInvitation.Status.PENDING:
            raise ValidationError("Only an invitation awaiting review can be withdrawn.")
        instance.status = OpportunityCollegeInvitation.Status.WITHDRAWN
        instance.save(update_fields=("status", "updated_at"))


class CollegeOpportunityInvitationListView(generics.ListAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = CollegeOpportunityInvitationSerializer
    queryset = OpportunityCollegeInvitation.objects.none()
    filterset_fields = ("status",)
    search_fields = ("opportunity__title", "opportunity__company__name", "opportunity__location")
    ordering_fields = ("submitted_at", "updated_at", "opportunity__application_deadline")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        queryset = OpportunityCollegeInvitation.objects.select_related(
            "opportunity", "opportunity__company", "college",
        ).prefetch_related("eligible_programs", "opportunity__required_skills")
        admin_profile = getattr(self.request.user, "college_admin_profile", None)
        if self.request.user.is_superuser and admin_profile is None:
            return queryset
        if admin_profile is None:
            return queryset.none()
        return queryset.filter(college=admin_profile.college)


class CollegeOpportunityInvitationReviewView(generics.GenericAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = CollegeOpportunityReviewSerializer

    def get_queryset(self):
        queryset = OpportunityCollegeInvitation.objects.select_related(
            "opportunity", "opportunity__company", "college",
        ).prefetch_related("eligible_programs", "opportunity__required_skills")
        admin_profile = getattr(self.request.user, "college_admin_profile", None)
        if self.request.user.is_superuser and admin_profile is None:
            return queryset
        if admin_profile is None:
            return queryset.none()
        return queryset.filter(college=admin_profile.college)

    def patch(self, request, *args, **kwargs):
        invitation = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        serializer = self.get_serializer(invitation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()
        invitation = self.get_queryset().get(pk=invitation.pk)
        return Response(CollegeOpportunityInvitationSerializer(invitation).data)


class StudentOpportunityListView(generics.ListAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentOpportunitySerializer
    search_fields = ("title", "company__name", "location", "required_skills__name")
    filterset_class = StudentOpportunityFilter
    ordering_fields = ("published_at", "application_deadline", "compensation_max")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return opportunity_queryset.none()
        return student_opportunity_queryset(self.request.user)


class StudentRecommendedOpportunityListView(generics.GenericAPIView):
    permission_classes = (IsStudent,)
    serializer_class = RecommendedOpportunitySerializer

    def get(self, request):
        queryset = student_opportunity_queryset(request.user)
        recommendations = get_recommended_opportunities(queryset, request.user.student_profile)
        return Response(self.get_serializer(recommendations, many=True).data)


class StudentOpportunityBookmarkView(generics.GenericAPIView):
    permission_classes = (IsStudent,)
    serializer_class = OpportunityBookmarkStateSerializer

    def get_opportunity(self):
        return get_object_or_404(student_opportunity_queryset(self.request.user), pk=self.kwargs["pk"])

    def post(self, request, *args, **kwargs):
        opportunity = self.get_opportunity()
        OpportunityBookmark.objects.get_or_create(student=request.user.student_profile, opportunity=opportunity)
        return Response({"opportunity_id": opportunity.id, "is_saved": True})

    def delete(self, request, *args, **kwargs):
        opportunity = self.get_opportunity()
        OpportunityBookmark.objects.filter(student=request.user.student_profile, opportunity=opportunity).delete()
        return Response({"opportunity_id": opportunity.id, "is_saved": False})


class StudentOpportunityDetailView(generics.RetrieveAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentOpportunitySerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return opportunity_queryset.none()
        return student_opportunity_queryset(self.request.user)
