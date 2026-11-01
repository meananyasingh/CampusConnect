import csv

from django.db.models import Q
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from accounts.permissions import IsCollegeAdmin

from .models import AuditEvent
from .serializers import AuditEventSerializer


def college_events(request):
    profile = getattr(request.user, "college_admin_profile", None)
    if profile is None:
        return AuditEvent.objects.none()
    queryset = AuditEvent.objects.filter(college=profile.college).select_related("actor")
    search = request.query_params.get("search", "").strip()
    if search:
        queryset = queryset.filter(
            Q(actor_email__icontains=search) | Q(actor_name__icontains=search)
            | Q(action__icontains=search) | Q(description__icontains=search)
            | Q(target_label__icontains=search)
        )
    if category := request.query_params.get("category"):
        queryset = queryset.filter(category=category)
    if role := request.query_params.get("actor_role"):
        queryset = queryset.filter(actor_role=role)
    if date_from := parse_date(request.query_params.get("date_from", "")):
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to := parse_date(request.query_params.get("date_to", "")):
        queryset = queryset.filter(created_at__date__lte=date_to)
    return queryset


def csv_safe(value):
    text = str(value or "")
    return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text


class CollegeAuditEventListView(generics.ListAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = AuditEventSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return AuditEvent.objects.none()
        return college_events(self.request)


class CollegeAuditExportView(generics.GenericAPIView):
    permission_classes = (IsCollegeAdmin,)

    @extend_schema(responses={(200, "text/csv"): OpenApiTypes.BINARY})
    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="campusconnect-audit-log.csv"'
        writer = csv.writer(response)
        writer.writerow(("Date", "Actor", "Role", "Category", "Action", "Target", "Changed fields", "IP address"))
        for event in college_events(request)[:10000]:
            writer.writerow(tuple(csv_safe(value) for value in (
                event.created_at.isoformat(), event.actor_email, event.actor_role,
                event.get_category_display(), event.action, event.target_label,
                ", ".join(event.changed_fields), event.ip_address or "",
            )))
        return response
