from django.urls import path

from .views import (
    CollegeOpportunityInvitationListView,
    CollegeOpportunityInvitationReviewView,
    RecruiterOpportunityDetailView,
    RecruiterOpportunityCollegeShareView,
    RecruiterOpportunityInvitationDetailView,
    RecruiterOpportunityListCreateView,
    StudentOpportunityBookmarkView,
    StudentOpportunityDetailView,
    StudentOpportunityListView,
    StudentRecommendedOpportunityListView,
)


urlpatterns = [
    path("recruiter/", RecruiterOpportunityListCreateView.as_view(), name="recruiter-opportunity-list"),
    path("recruiter/<int:pk>/", RecruiterOpportunityDetailView.as_view(), name="recruiter-opportunity-detail"),
    path("recruiter/<int:pk>/colleges/", RecruiterOpportunityCollegeShareView.as_view(), name="recruiter-opportunity-college-share"),
    path("recruiter/invitations/<int:pk>/", RecruiterOpportunityInvitationDetailView.as_view(), name="recruiter-opportunity-invitation-detail"),
    path("admin/invitations/", CollegeOpportunityInvitationListView.as_view(), name="admin-opportunity-invitation-list"),
    path("admin/invitations/<int:pk>/", CollegeOpportunityInvitationReviewView.as_view(), name="admin-opportunity-invitation-review"),
    path("student/", StudentOpportunityListView.as_view(), name="student-opportunity-list"),
    path("student/recommended/", StudentRecommendedOpportunityListView.as_view(), name="student-opportunity-recommended"),
    path("student/<int:pk>/save/", StudentOpportunityBookmarkView.as_view(), name="student-opportunity-save"),
    path("student/<int:pk>/", StudentOpportunityDetailView.as_view(), name="student-opportunity-detail"),
]
