from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from accounts.permissions import IsCollegeAdmin, IsRecruiter, IsStudent
from notifications.models import Notification
from notifications.services import notify_company_recruiters

from .models import Announcement, AnnouncementRead
from .serializers import AnnouncementReviewSerializer, AnnouncementSerializer
from .services import notify_announcement_students, notify_pending_announcement


announcement_queryset = Announcement.objects.select_related(
    "college", "company", "created_by", "reviewed_by", "related_opportunity",
    "related_opportunity__company", "related_drive",
).prefetch_related("target_programs", "read_receipts")


def admin_college(user):
    profile = getattr(user, "college_admin_profile", None)
    if profile is None:
        raise PermissionDenied("Configure a college admin profile first.")
    return profile.college


def visible_to_student(user):
    now = timezone.now()
    student = user.student_profile
    candidates = announcement_queryset.filter(
        college=student.college,
        approval_status=Announcement.ApprovalStatus.APPROVED,
        publish_at__lte=now,
        is_archived=False,
    ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now)).filter(
        Q(target_programs__isnull=True) | Q(target_programs=student.program),
    ).distinct()
    return [item for item in candidates if not item.target_graduation_years or student.graduation_year in item.target_graduation_years]


class AdminAnnouncementListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = AnnouncementSerializer
    pagination_class = None
    filterset_fields = ("approval_status", "announcement_type", "priority", "is_archived")
    search_fields = ("title", "body", "company__name")

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return announcement_queryset.none()
        return announcement_queryset.filter(college=admin_college(self.request.user))

    def perform_create(self, serializer):
        announcement = serializer.save(
            college=admin_college(self.request.user),
            created_by=self.request.user,
            approval_status=Announcement.ApprovalStatus.APPROVED,
            reviewed_by=self.request.user,
            reviewed_at=timezone.now(),
        )
        notify_announcement_students(announcement)


class AdminAnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = AnnouncementSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return announcement_queryset.none()
        return announcement_queryset.filter(college=admin_college(self.request.user))


class AdminAnnouncementReviewView(generics.GenericAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = AnnouncementReviewSerializer

    def post(self, request, *args, **kwargs):
        announcement = get_object_or_404(
            announcement_queryset.filter(college=admin_college(request.user)), pk=self.kwargs["pk"],
        )
        serializer = self.get_serializer(data=request.data, context={"announcement": announcement})
        serializer.is_valid(raise_exception=True)
        announcement.approval_status = serializer.validated_data["approval_status"]
        announcement.review_note = serializer.validated_data.get("review_note", "")
        announcement.reviewed_by = request.user
        announcement.reviewed_at = timezone.now()
        announcement.save(update_fields=("approval_status", "review_note", "reviewed_by", "reviewed_at", "updated_at"))
        if announcement.approval_status == Announcement.ApprovalStatus.APPROVED:
            notify_announcement_students(announcement)
        if announcement.company:
            notify_company_recruiters(
                company=announcement.company,
                category=Notification.Category.ANNOUNCEMENT,
                title=f"Announcement {announcement.get_approval_status_display().lower()}",
                message=f"{announcement.college.name} reviewed “{announcement.title}”.",
                link="/recruiter/announcements",
            )
        return Response(AnnouncementSerializer(announcement, context={"request": request}).data)


class RecruiterAnnouncementListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = AnnouncementSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return announcement_queryset.none()
        return announcement_queryset.filter(company=self.request.user.recruiter_profile.company)

    def perform_create(self, serializer):
        announcement = serializer.save(
            company=self.request.user.recruiter_profile.company,
            created_by=self.request.user,
            approval_status=Announcement.ApprovalStatus.PENDING,
        )
        notify_pending_announcement(announcement)


class RecruiterAnnouncementDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = AnnouncementSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return announcement_queryset.none()
        return announcement_queryset.filter(company=self.request.user.recruiter_profile.company)

    def perform_update(self, serializer):
        if serializer.instance.approval_status != Announcement.ApprovalStatus.PENDING:
            raise ValidationError("Only a pending announcement can be edited.")
        serializer.save(approval_status=Announcement.ApprovalStatus.PENDING)

    def perform_destroy(self, instance):
        if instance.approval_status != Announcement.ApprovalStatus.PENDING:
            raise ValidationError("Only a pending announcement can be deleted.")
        instance.delete()


class StudentAnnouncementListView(generics.GenericAPIView):
    permission_classes = (IsStudent,)
    serializer_class = AnnouncementSerializer

    def get(self, request):
        return Response(self.get_serializer(visible_to_student(request.user), many=True).data)


class StudentAnnouncementReadView(generics.GenericAPIView):
    permission_classes = (IsStudent,)
    serializer_class = AnnouncementSerializer

    def post(self, request, *args, **kwargs):
        announcement = next(
            (item for item in visible_to_student(request.user) if item.pk == self.kwargs["pk"]),
            None,
        )
        if announcement is None:
            raise Http404
        AnnouncementRead.objects.get_or_create(announcement=announcement, user=request.user)
        announcement._prefetched_objects_cache.pop("read_receipts", None)
        return Response(self.get_serializer(announcement).data)
