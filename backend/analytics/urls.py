from django.urls import path

from .views import (
    ApplicationCsvReportView,
    CollegeAnalyticsView,
    PlacementCsvReportView,
    RecruiterDashboardView,
    StudentDashboardView,
    StudentCsvReportView,
)


urlpatterns = [
    path("student/dashboard/", StudentDashboardView.as_view(), name="student-dashboard"),
    path("recruiter/dashboard/", RecruiterDashboardView.as_view(), name="recruiter-dashboard"),
    path("admin/overview/", CollegeAnalyticsView.as_view(), name="college-analytics"),
    path("admin/reports/students/", StudentCsvReportView.as_view(), name="student-csv-report"),
    path("admin/reports/applications/", ApplicationCsvReportView.as_view(), name="application-csv-report"),
    path("admin/reports/placements/", PlacementCsvReportView.as_view(), name="placement-csv-report"),
]
