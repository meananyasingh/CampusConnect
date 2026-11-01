from django.urls import path

from .views import (
    CollegeCompanyPartnershipDetailView,
    CollegeCompanyPartnershipListView,
    OwnCompanyView,
    OwnRecruiterProfileView,
    RecruiterPartnershipDetailView,
    RecruiterPartnershipListCreateView,
)


urlpatterns = [
    path("recruiter/profile/", OwnRecruiterProfileView.as_view(), name="recruiter-profile"),
    path("recruiter/company/", OwnCompanyView.as_view(), name="recruiter-company"),
    path("recruiter/partnerships/", RecruiterPartnershipListCreateView.as_view(), name="recruiter-partnership-list"),
    path("recruiter/partnerships/<int:pk>/", RecruiterPartnershipDetailView.as_view(), name="recruiter-partnership-detail"),
    path("admin/partnerships/", CollegeCompanyPartnershipListView.as_view(), name="admin-company-partnership-list"),
    path("admin/partnerships/<int:pk>/", CollegeCompanyPartnershipDetailView.as_view(), name="admin-company-partnership-detail"),
]
