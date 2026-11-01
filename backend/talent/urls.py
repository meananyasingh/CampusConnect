from django.urls import path

from .views import (
    RecruiterCandidateDetailView,
    RecruiterCandidateListView,
    RecruiterCandidateResumeView,
    RecruiterTalentPoolDetailView,
    RecruiterTalentPoolListCreateView,
    RecruiterTalentPoolMemberCreateView,
    RecruiterTalentPoolMemberDetailView,
)


urlpatterns = [
    path("recruiter/candidates/", RecruiterCandidateListView.as_view(), name="talent-candidate-list"),
    path("recruiter/candidates/<int:pk>/", RecruiterCandidateDetailView.as_view(), name="talent-candidate-detail"),
    path("recruiter/candidates/<int:pk>/resume/", RecruiterCandidateResumeView.as_view(), name="talent-candidate-resume"),
    path("recruiter/pools/", RecruiterTalentPoolListCreateView.as_view(), name="talent-pool-list"),
    path("recruiter/pools/<int:pk>/", RecruiterTalentPoolDetailView.as_view(), name="talent-pool-detail"),
    path("recruiter/pools/<int:pool_pk>/members/", RecruiterTalentPoolMemberCreateView.as_view(), name="talent-pool-member-create"),
    path("recruiter/pools/<int:pool_pk>/members/<int:pk>/", RecruiterTalentPoolMemberDetailView.as_view(), name="talent-pool-member-detail"),
]

