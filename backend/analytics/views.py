import csv
from datetime import timedelta

from django.db.models import Avg, Count, Max, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from accounts.permissions import IsCollegeAdmin, IsRecruiter, IsStudent
from announcements.views import visible_to_student
from applications.models import Application, InterviewSchedule
from colleges.models import AcademicProgram
from companies.models import CompanyCollegePartnership
from opportunities.models import Opportunity
from opportunities.services import get_recommended_opportunities
from placements.models import PlacementRecord
from students.models import StudentProfile
from students.services import calculate_profile_completion

from .serializers import (
    CollegeAnalyticsSerializer,
    RecruiterDashboardSerializer,
    StudentDashboardSerializer,
)


def get_admin_college(user):
    profile = getattr(user, "college_admin_profile", None)
    if profile is None:
        raise PermissionDenied("Configure a college admin profile before viewing analytics.")
    return profile.college


class StudentDashboardView(generics.GenericAPIView):
    permission_classes = (IsStudent,)
    serializer_class = StudentDashboardSerializer

    def get(self, request):
        student = request.user.student_profile
        applications = Application.objects.select_related(
            "opportunity", "opportunity__company", "student", "student__user",
            "student__college", "student__program", "resume",
        ).prefetch_related("status_history", "status_history__changed_by").filter(student=student)
        interviews = InterviewSchedule.objects.select_related(
            "recruitment_round", "recruitment_round__opportunity",
            "application", "application__opportunity", "application__opportunity__company",
        ).filter(application__student=student)
        upcoming_interviews = interviews.filter(
            status=InterviewSchedule.Status.SCHEDULED,
            scheduled_at__gte=timezone.now(),
        )

        available = Opportunity.objects.select_related("company", "created_by").prefetch_related(
            "target_colleges", "eligible_programs", "required_skills",
        ).filter(
            status=Opportunity.Status.PUBLISHED,
            application_deadline__gte=timezone.localdate(),
            company__is_active=True,
            target_colleges=student.college,
            company__college_partnerships__college=student.college,
            company__college_partnerships__status=CompanyCollegePartnership.Status.VERIFIED,
        ).exclude(applications__student=student).distinct()
        recommendations = get_recommended_opportunities(available, student, limit=4)

        active_review_statuses = (
            Application.Status.APPLIED,
            Application.Status.UNDER_REVIEW,
            Application.Status.INTERVIEW,
        )
        data = {
            "profile_completion": calculate_profile_completion(student)["percentage"],
            "stats": {
                "total_applications": applications.count(),
                "under_review": applications.filter(status__in=active_review_statuses).count(),
                "shortlisted": applications.filter(status=Application.Status.SHORTLISTED).count(),
                "upcoming_interviews": upcoming_interviews.count(),
                "selected": applications.filter(status=Application.Status.SELECTED).count(),
            },
            "recent_applications": applications[:4],
            "upcoming_interviews": upcoming_interviews.order_by("scheduled_at")[:3],
            "recommended_opportunities": recommendations,
            "announcements": visible_to_student(request.user)[:3],
        }
        return Response(self.get_serializer(data, context={"request": request}).data)


class RecruiterDashboardView(generics.GenericAPIView):
    permission_classes = (IsRecruiter,)
    serializer_class = RecruiterDashboardSerializer

    def get(self, request):
        company = request.user.recruiter_profile.company
        applications = Application.objects.select_related(
            "opportunity", "opportunity__company", "student", "student__user",
            "student__college", "student__program", "resume",
        ).prefetch_related("status_history", "status_history__changed_by").filter(
            opportunity__company=company,
        )
        upcoming_interviews = InterviewSchedule.objects.select_related(
            "recruitment_round", "recruitment_round__opportunity", "application",
            "application__opportunity", "application__opportunity__company",
        ).filter(
            application__opportunity__company=company,
            status=InterviewSchedule.Status.SCHEDULED,
            scheduled_at__gte=timezone.now(),
        )
        opportunities = Opportunity.objects.filter(company=company).annotate(
            total_applications=Count("applications"),
            shortlisted=Count("applications", filter=Q(applications__status=Application.Status.SHORTLISTED)),
            selected=Count("applications", filter=Q(applications__status=Application.Status.SELECTED)),
        ).order_by("-total_applications", "-created_at")
        performance = [
            {
                "id": item.id,
                "title": item.title,
                "status": item.status,
                "status_display": item.get_status_display(),
                "total_applications": item.total_applications,
                "shortlisted": item.shortlisted,
                "selected": item.selected,
            }
            for item in opportunities[:5]
        ]
        data = {
            "company": company,
            "stats": {
                "total_applications": applications.count(),
                "under_review": applications.filter(status=Application.Status.UNDER_REVIEW).count(),
                "shortlisted": applications.filter(status=Application.Status.SHORTLISTED).count(),
                "upcoming_interviews": upcoming_interviews.count(),
                "selected": applications.filter(status=Application.Status.SELECTED).count(),
                "active_opportunities": opportunities.filter(status=Opportunity.Status.PUBLISHED).count(),
                "verified_colleges": company.college_partnerships.filter(
                    status=CompanyCollegePartnership.Status.VERIFIED,
                ).count(),
            },
            "recent_applications": applications[:5],
            "upcoming_interviews": upcoming_interviews.order_by("scheduled_at")[:4],
            "opportunity_performance": performance,
        }
        return Response(self.get_serializer(data, context={"request": request}).data)


class CollegeAnalyticsView(generics.GenericAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = CollegeAnalyticsSerializer

    def get(self, request):
        college = get_admin_college(request.user)
        active_placement_filter = Q(
            students__applications__placement_record__isnull=False,
        ) & ~Q(
            students__applications__placement_record__status__in=(
                PlacementRecord.Status.DECLINED,
                PlacementRecord.Status.CANCELLED,
            )
        )
        branches = AcademicProgram.objects.filter(college=college).annotate(
            total_students=Count("students", distinct=True),
            placed_students=Count(
                "students",
                filter=active_placement_filter,
                distinct=True,
            ),
        )
        branch_performance = [
            {
                "name": f"{program.get_degree_display()} — {program.branch}",
                "total_students": program.total_students,
                "placed_students": program.placed_students,
                "placement_percentage": round(
                    program.placed_students / program.total_students * 100, 2
                ) if program.total_students else 0,
            }
            for program in branches
        ]

        applications = Application.objects.filter(student__college=college)
        pipeline_counts = {
            row["status"]: row["count"]
            for row in applications.values("status").annotate(count=Count("id"))
        }
        status_labels = dict(Application.Status.choices)
        application_pipeline = [
            {"name": status_labels[status], "count": pipeline_counts.get(status, 0)}
            for status in Application.Status.values
        ]

        active_placements = PlacementRecord.objects.filter(college=college).exclude(
            status__in=(PlacementRecord.Status.DECLINED, PlacementRecord.Status.CANCELLED),
        )
        company_placements = [
            {
                "name": row["application__opportunity__company__name"],
                "placed_students": row["placed_students"],
                "average_package": row["average_package"],
                "highest_package": row["highest_package"],
            }
            for row in active_placements.values(
                "application__opportunity__company__name"
            ).annotate(
                placed_students=Count("application__student", distinct=True),
                average_package=Avg("annual_package"),
                highest_package=Max("annual_package"),
            ).order_by("-placed_students", "application__opportunity__company__name")
        ]

        start_date = timezone.localdate().replace(day=1) - timedelta(days=365)
        monthly_applications = [
            {"month": row["month"].date(), "applications": row["applications"]}
            for row in applications.filter(applied_at__date__gte=start_date).annotate(
                month=TruncMonth("applied_at")
            ).values("month").annotate(applications=Count("id")).order_by("month")
        ]
        return Response({
            "application_pipeline": application_pipeline,
            "branch_performance": branch_performance,
            "company_placements": company_placements,
            "monthly_applications": monthly_applications,
        })


class CollegeCsvReportView(generics.GenericAPIView):
    permission_classes = (IsCollegeAdmin,)
    serializer_class = CollegeAnalyticsSerializer
    report_type = None

    @extend_schema(responses={(200, "text/csv"): OpenApiTypes.BINARY})
    def get(self, request):
        college = get_admin_college(request.user)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="campusconnect-{self.report_type}.csv"'
        writer = csv.writer(response)
        getattr(self, f"write_{self.report_type}")(writer, college)
        return response

    @staticmethod
    def write_students(writer, college):
        writer.writerow(("Student", "Email", "Enrollment", "Program", "Graduation Year", "CGPA", "Active Backlogs", "Account Active"))
        for student in StudentProfile.objects.select_related("user", "program").filter(college=college):
            writer.writerow((
                student.user.get_full_name(), student.user.email, student.enrollment_number,
                str(student.program), student.graduation_year, student.cgpa or "",
                student.active_backlogs, "Yes" if student.user.is_active else "No",
            ))

    @staticmethod
    def write_applications(writer, college):
        writer.writerow(("Student", "Enrollment", "Company", "Opportunity", "Status", "Applied At"))
        for application in Application.objects.select_related(
            "student__user", "opportunity__company"
        ).filter(student__college=college):
            writer.writerow((
                application.student.user.get_full_name(), application.student.enrollment_number,
                application.opportunity.company.name, application.opportunity.title,
                application.get_status_display(), application.applied_at.isoformat(),
            ))

    @staticmethod
    def write_placements(writer, college):
        writer.writerow(("Student", "Enrollment", "Company", "Opportunity", "Annual Package", "Offer Date", "Joining Date", "Status"))
        for placement in PlacementRecord.objects.select_related(
            "application__student__user", "application__opportunity__company"
        ).filter(college=college):
            application = placement.application
            writer.writerow((
                application.student.user.get_full_name(), application.student.enrollment_number,
                application.opportunity.company.name, application.opportunity.title,
                placement.annual_package, placement.offer_date,
                placement.joining_date or "", placement.get_status_display(),
            ))


class StudentCsvReportView(CollegeCsvReportView):
    report_type = "students"


class ApplicationCsvReportView(CollegeCsvReportView):
    report_type = "applications"


class PlacementCsvReportView(CollegeCsvReportView):
    report_type = "placements"
