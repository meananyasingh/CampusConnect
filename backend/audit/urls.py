from django.urls import path

from .views import CollegeAuditEventListView, CollegeAuditExportView


urlpatterns = [
    path("admin/", CollegeAuditEventListView.as_view(), name="audit-event-list"),
    path("admin/export/", CollegeAuditExportView.as_view(), name="audit-event-export"),
]
