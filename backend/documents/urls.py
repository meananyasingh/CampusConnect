from django.urls import path

from .views import (
    AdminStudentDocumentDownloadView,
    AdminStudentDocumentListView,
    AdminStudentDocumentReviewView,
    StudentDocumentDetailView,
    StudentDocumentDownloadView,
    StudentDocumentListCreateView,
    StudentDocumentSummaryView,
)


urlpatterns = [
    path("student/", StudentDocumentListCreateView.as_view(), name="student-document-list"),
    path("student/summary/", StudentDocumentSummaryView.as_view(), name="student-document-summary"),
    path("student/<int:pk>/", StudentDocumentDetailView.as_view(), name="student-document-detail"),
    path("student/<int:pk>/download/", StudentDocumentDownloadView.as_view(), name="student-document-download"),
    path("admin/", AdminStudentDocumentListView.as_view(), name="admin-document-list"),
    path("admin/<int:pk>/", AdminStudentDocumentReviewView.as_view(), name="admin-document-review"),
    path("admin/<int:pk>/download/", AdminStudentDocumentDownloadView.as_view(), name="admin-document-download"),
]

