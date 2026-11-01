from django.db.models import Count, Prefetch, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics

from accounts.permissions import IsRecruiter
from students.models import StudentProfile

from .filters import RecruiterCandidateFilter
from .models import TalentPool, TalentPoolMember
from .serializers import (
    CandidateDetailSerializer,
    CandidateSummarySerializer,
    TalentPoolMemberSerializer,
    TalentPoolSerializer,
)
from .services import recruiter_candidate_queryset


def recruiter_pool_queryset(user):
    accessible_students = recruiter_candidate_queryset(user)
    accessible_members = TalentPoolMember.objects.filter(
        student__in=accessible_students,
    ).select_related("student__user", "student__college", "student__program").prefetch_related(
        "student__skills__skill", "student__resumes", "student__projects",
        "student__certifications", "student__experiences",
    )
    return TalentPool.objects.filter(
        company=user.recruiter_profile.company
    ).annotate(
        member_count=Count(
            "members",
            filter=Q(members__student__in=accessible_students),
            distinct=True,
        )
    ).prefetch_related(Prefetch("members", queryset=accessible_members))


class RecruiterCandidateListView(generics.ListAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = CandidateSummarySerializer
    filterset_class = RecruiterCandidateFilter
    search_fields = (
        "user__first_name", "user__last_name", "college__name", "program__branch",
        "preferred_job_role", "skills__skill__name",
    )
    ordering_fields = ("user__first_name", "graduation_year", "cgpa", "updated_at")
    ordering = ("user__first_name", "user__last_name")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudentProfile.objects.none()
        return recruiter_candidate_queryset(self.request.user)


class RecruiterCandidateDetailView(generics.RetrieveAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = CandidateDetailSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudentProfile.objects.none()
        return recruiter_candidate_queryset(self.request.user).prefetch_related(
            "projects", "certifications", "experiences"
        )


class RecruiterCandidateResumeView(generics.GenericAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = CandidateDetailSerializer

    def get(self, request, pk):
        student = get_object_or_404(recruiter_candidate_queryset(request.user), pk=pk)
        resume = get_object_or_404(student.resumes, is_primary=True)
        return FileResponse(
            resume.file.open("rb"),
            as_attachment=True,
            filename=resume.original_filename,
            content_type="application/pdf",
        )


class RecruiterTalentPoolListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = TalentPoolSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return TalentPool.objects.none()
        return recruiter_pool_queryset(self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            company=self.request.user.recruiter_profile.company,
            created_by=self.request.user,
        )


class RecruiterTalentPoolDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = TalentPoolSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return TalentPool.objects.none()
        return recruiter_pool_queryset(self.request.user)


class RecruiterTalentPoolMemberCreateView(generics.CreateAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = TalentPoolMemberSerializer

    def get_pool(self):
        return get_object_or_404(
            TalentPool,
            pk=self.kwargs["pool_pk"],
            company=self.request.user.recruiter_profile.company,
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["pool"] = self.get_pool()
        return context

    def perform_create(self, serializer):
        serializer.save(pool=self.get_pool(), added_by=self.request.user)


class RecruiterTalentPoolMemberDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = TalentPoolMemberSerializer
    http_method_names = ("patch", "delete", "options")

    def get_queryset(self):
        return TalentPoolMember.objects.filter(
            pool_id=self.kwargs["pool_pk"],
            pool__company=self.request.user.recruiter_profile.company,
            student__in=recruiter_candidate_queryset(self.request.user),
        ).select_related("student__user", "student__college", "student__program")
