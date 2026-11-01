from django.urls import path

from .views import ActiveAcademicProgramListView, ActiveCollegeListView


urlpatterns = [
    path("", ActiveCollegeListView.as_view(), name="college-list"),
    path("programs/", ActiveAcademicProgramListView.as_view(), name="program-list"),
]
