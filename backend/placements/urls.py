from django.urls import path

from .views import (
    CollegeApplicationListView,
    CollegeDashboardView,
    CollegeInterviewListView,
    CollegeDriveOpportunityListView,
    CollegePlacementDetailView,
    CollegePlacementDriveDetailView,
    CollegePlacementDriveListCreateView,
    CollegePlacementListCreateView,
    CollegePlacementPolicyView,
    RecruiterPlacementDriveListView,
    StudentPlacementDecisionView,
    StudentPlacementDriveListView,
    StudentPlacementListView,
    StudentPlacementReadinessView,
)


urlpatterns = [
    path("admin/dashboard/", CollegeDashboardView.as_view(), name="college-dashboard"),
    path("admin/policy/", CollegePlacementPolicyView.as_view(), name="college-placement-policy"),
    path("admin/drive-opportunities/", CollegeDriveOpportunityListView.as_view(), name="college-drive-opportunity-list"),
    path("admin/drives/", CollegePlacementDriveListCreateView.as_view(), name="college-drive-list"),
    path("admin/drives/<int:pk>/", CollegePlacementDriveDetailView.as_view(), name="college-drive-detail"),
    path("admin/applications/", CollegeApplicationListView.as_view(), name="college-application-list"),
    path("admin/interviews/", CollegeInterviewListView.as_view(), name="college-interview-list"),
    path("admin/records/", CollegePlacementListCreateView.as_view(), name="college-placement-list"),
    path("admin/records/<int:pk>/", CollegePlacementDetailView.as_view(), name="college-placement-detail"),
    path("student/", StudentPlacementListView.as_view(), name="student-placement-list"),
    path("student/readiness/", StudentPlacementReadinessView.as_view(), name="student-placement-readiness"),
    path("student/drives/", StudentPlacementDriveListView.as_view(), name="student-drive-list"),
    path("student/<int:pk>/decision/", StudentPlacementDecisionView.as_view(), name="student-placement-decision"),
    path("recruiter/drives/", RecruiterPlacementDriveListView.as_view(), name="recruiter-drive-list"),
]
