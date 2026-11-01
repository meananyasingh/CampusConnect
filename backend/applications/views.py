from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsRecruiter, IsStudent
from notifications.models import Notification
from notifications.services import notify_company_recruiters

from .models import Application, ApplicationStatusHistory, InterviewSchedule, RecruitmentRound
from .serializers import (
    ApplicationSerializer,
    InterviewScheduleSerializer,
    RecruiterApplicationStatusSerializer,
    RecruitmentRoundSerializer,
    StudentInterviewScheduleSerializer,
)


application_queryset = Application.objects.select_related(
    "opportunity", "opportunity__company", "student", "student__user",
    "student__college", "student__program", "resume",
).prefetch_related("status_history", "status_history__changed_by")

round_queryset = RecruitmentRound.objects.select_related(
    "opportunity", "opportunity__company", "created_by",
).annotate(interview_count=Count("interviews"))

interview_queryset = InterviewSchedule.objects.select_related(
    "recruitment_round", "recruitment_round__opportunity",
    "recruitment_round__opportunity__company", "application",
    "application__opportunity", "application__opportunity__company",
    "application__student", "application__student__user", "application__student__college",
    "application__student__program", "application__resume", "created_by",
).prefetch_related("application__status_history", "application__status_history__changed_by")


class StudentApplicationListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsStudent,)
    serializer_class = ApplicationSerializer
    filterset_fields = ("status", "opportunity__opportunity_type")
    ordering_fields = ("applied_at", "updated_at")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return application_queryset.none()
        return application_queryset.filter(student__user=self.request.user)


class StudentApplicationDetailView(generics.RetrieveAPIView):
    permission_classes = (IsStudent,)
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return application_queryset.none()
        return application_queryset.filter(student__user=self.request.user)


class StudentApplicationWithdrawView(generics.GenericAPIView):
    permission_classes = (IsStudent,)
    serializer_class = ApplicationSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        application = get_object_or_404(
            application_queryset.filter(student__user=request.user),
            pk=self.kwargs["pk"],
        )
        if application.status not in {
            Application.Status.APPLIED,
            Application.Status.UNDER_REVIEW,
            Application.Status.SHORTLISTED,
        }:
            raise ValidationError("This application can no longer be withdrawn.")
        previous_status = application.status
        application.status = Application.Status.WITHDRAWN
        application.save(update_fields=("status", "updated_at"))
        ApplicationStatusHistory.objects.create(
            application=application,
            from_status=previous_status,
            to_status=Application.Status.WITHDRAWN,
            changed_by=request.user,
            note="Application withdrawn by student.",
        )
        notify_company_recruiters(
            company=application.opportunity.company,
            category=Notification.Category.APPLICATION,
            title="Application withdrawn",
            message=f"A student withdrew their application for {application.opportunity.title}.",
            link=f"/recruiter/applications?opportunity={application.opportunity_id}",
        )
        application._prefetched_objects_cache = {}
        return Response(ApplicationSerializer(application, context={"request": request}).data)


class RecruiterApplicationListView(generics.ListAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = ApplicationSerializer
    filterset_fields = ("status", "opportunity")
    search_fields = (
        "student__user__first_name", "student__user__last_name",
        "student__user__email", "student__enrollment_number", "opportunity__title",
    )
    ordering_fields = ("applied_at", "updated_at", "student__cgpa")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return application_queryset.none()
        return application_queryset.filter(
            opportunity__company=self.request.user.recruiter_profile.company,
        )


class RecruiterApplicationDetailView(generics.GenericAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = RecruiterApplicationStatusSerializer

    def get_object(self):
        return get_object_or_404(
            application_queryset.filter(
                opportunity__company=self.request.user.recruiter_profile.company,
            ),
            pk=self.kwargs["pk"],
        )

    def get(self, request, *args, **kwargs):
        return Response(ApplicationSerializer(self.get_object(), context={"request": request}).data)

    def patch(self, request, *args, **kwargs):
        application = self.get_object()
        serializer = self.get_serializer(
            data=request.data,
            context={**self.get_serializer_context(), "application": application},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ApplicationSerializer(application, context={"request": request}).data)


class RecruiterRoundListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = RecruitmentRoundSerializer
    pagination_class = None
    filterset_fields = ("opportunity", "round_type")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return round_queryset.none()
        return round_queryset.filter(
            opportunity__company=self.request.user.recruiter_profile.company,
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class RecruiterRoundDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = RecruitmentRoundSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return round_queryset.none()
        return round_queryset.filter(
            opportunity__company=self.request.user.recruiter_profile.company,
        )

    def perform_destroy(self, instance):
        if instance.interviews.exists():
            raise ValidationError("A round with scheduled interviews cannot be deleted.")
        instance.delete()


class RecruiterInterviewListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = InterviewScheduleSerializer
    filterset_fields = (
        "status", "result", "mode", "recruitment_round",
        "application", "application__opportunity",
    )
    search_fields = (
        "application__student__user__first_name", "application__student__user__last_name",
        "application__student__user__email", "application__student__enrollment_number",
    )
    ordering_fields = ("scheduled_at", "created_at")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return interview_queryset.none()
        return interview_queryset.filter(
            application__opportunity__company=self.request.user.recruiter_profile.company,
        )


class RecruiterInterviewDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = InterviewScheduleSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return interview_queryset.none()
        return interview_queryset.filter(
            application__opportunity__company=self.request.user.recruiter_profile.company,
        )


class StudentInterviewListView(generics.ListAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentInterviewScheduleSerializer
    filterset_fields = ("status", "result")
    ordering_fields = ("scheduled_at",)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return interview_queryset.none()
        return interview_queryset.filter(application__student__user=self.request.user)


class StudentInterviewDetailView(generics.RetrieveAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentInterviewScheduleSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return interview_queryset.none()
        return interview_queryset.filter(application__student__user=self.request.user)
