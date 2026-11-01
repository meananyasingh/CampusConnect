from django.urls import path

from .views import (
    AdminAnnouncementDetailView,
    AdminAnnouncementListCreateView,
    AdminAnnouncementReviewView,
    RecruiterAnnouncementDetailView,
    RecruiterAnnouncementListCreateView,
    StudentAnnouncementListView,
    StudentAnnouncementReadView,
)


urlpatterns = [
    path("admin/", AdminAnnouncementListCreateView.as_view(), name="admin-announcement-list"),
    path("admin/<int:pk>/", AdminAnnouncementDetailView.as_view(), name="admin-announcement-detail"),
    path("admin/<int:pk>/review/", AdminAnnouncementReviewView.as_view(), name="admin-announcement-review"),
    path("recruiter/", RecruiterAnnouncementListCreateView.as_view(), name="recruiter-announcement-list"),
    path("recruiter/<int:pk>/", RecruiterAnnouncementDetailView.as_view(), name="recruiter-announcement-detail"),
    path("student/", StudentAnnouncementListView.as_view(), name="student-announcement-list"),
    path("student/<int:pk>/read/", StudentAnnouncementReadView.as_view(), name="student-announcement-read"),
]
