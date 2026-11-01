from django.urls import path

from .views import (
    CollegeStudentListView,
    CollegeStudentDetailView,
    CollegeStudentActivationResendView,
    CollegeStudentImportConfirmView,
    CollegeStudentImportListCreateView,
    CollegeStudentImportTemplateView,
    OwnStudentProfileView,
    StudentCertificationDetailView,
    StudentCertificationListCreateView,
    StudentExperienceDetailView,
    StudentExperienceListCreateView,
    StudentProjectDetailView,
    StudentProjectListCreateView,
    StudentProfileCompletionView,
    StudentResumeDetailView,
    StudentResumeListCreateView,
    StudentSkillDetailView,
    StudentSkillListCreateView,
)


urlpatterns = [
    path("admin/imports/template/", CollegeStudentImportTemplateView.as_view(), name="college-student-import-template"),
    path("admin/imports/", CollegeStudentImportListCreateView.as_view(), name="college-student-import-list"),
    path("admin/imports/<int:pk>/confirm/", CollegeStudentImportConfirmView.as_view(), name="college-student-import-confirm"),
    path("<int:pk>/resend-activation/", CollegeStudentActivationResendView.as_view(), name="college-student-resend-activation"),
    path("profile/", OwnStudentProfileView.as_view(), name="student-profile"),
    path("profile-completion/", StudentProfileCompletionView.as_view(), name="student-profile-completion"),
    path("resumes/", StudentResumeListCreateView.as_view(), name="student-resume-list"),
    path("resumes/<int:pk>/", StudentResumeDetailView.as_view(), name="student-resume-detail"),
    path("portfolio/skills/", StudentSkillListCreateView.as_view(), name="student-skill-list"),
    path("portfolio/skills/<int:pk>/", StudentSkillDetailView.as_view(), name="student-skill-detail"),
    path("portfolio/projects/", StudentProjectListCreateView.as_view(), name="student-project-list"),
    path("portfolio/projects/<int:pk>/", StudentProjectDetailView.as_view(), name="student-project-detail"),
    path("portfolio/certifications/", StudentCertificationListCreateView.as_view(), name="student-certification-list"),
    path("portfolio/certifications/<int:pk>/", StudentCertificationDetailView.as_view(), name="student-certification-detail"),
    path("portfolio/experiences/", StudentExperienceListCreateView.as_view(), name="student-experience-list"),
    path("portfolio/experiences/<int:pk>/", StudentExperienceDetailView.as_view(), name="student-experience-detail"),
    path("<int:pk>/", CollegeStudentDetailView.as_view(), name="college-student-detail"),
    path("", CollegeStudentListView.as_view(), name="college-student-list"),
]
