from django.urls import path

from .views import (
    RecruiterApplicationDetailView,
    RecruiterApplicationListView,
    RecruiterInterviewDetailView,
    RecruiterInterviewListCreateView,
    RecruiterRoundDetailView,
    RecruiterRoundListCreateView,
    StudentApplicationDetailView,
    StudentApplicationListCreateView,
    StudentApplicationWithdrawView,
    StudentInterviewDetailView,
    StudentInterviewListView,
)


urlpatterns = [
    path("student/", StudentApplicationListCreateView.as_view(), name="student-application-list"),
    path("student/<int:pk>/", StudentApplicationDetailView.as_view(), name="student-application-detail"),
    path("student/<int:pk>/withdraw/", StudentApplicationWithdrawView.as_view(), name="student-application-withdraw"),
    path("student/interviews/", StudentInterviewListView.as_view(), name="student-interview-list"),
    path("student/interviews/<int:pk>/", StudentInterviewDetailView.as_view(), name="student-interview-detail"),
    path("recruiter/", RecruiterApplicationListView.as_view(), name="recruiter-application-list"),
    path("recruiter/<int:pk>/", RecruiterApplicationDetailView.as_view(), name="recruiter-application-detail"),
    path("recruiter/rounds/", RecruiterRoundListCreateView.as_view(), name="recruiter-round-list"),
    path("recruiter/rounds/<int:pk>/", RecruiterRoundDetailView.as_view(), name="recruiter-round-detail"),
    path("recruiter/interviews/", RecruiterInterviewListCreateView.as_view(), name="recruiter-interview-list"),
    path("recruiter/interviews/<int:pk>/", RecruiterInterviewDetailView.as_view(), name="recruiter-interview-detail"),
]
