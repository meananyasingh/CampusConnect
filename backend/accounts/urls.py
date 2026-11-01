from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdminLoginView,
    CurrentUserView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RecruiterLoginView,
    RecruiterRegistrationView,
    StudentLoginView,
    StudentRegistrationView,
)


urlpatterns = [
    path("student/register/", StudentRegistrationView.as_view(), name="student-register"),
    path("student/login/", StudentLoginView.as_view(), name="student-login"),
    path(
        "recruiter/register/",
        RecruiterRegistrationView.as_view(),
        name="recruiter-register",
    ),
    path("recruiter/login/", RecruiterLoginView.as_view(), name="recruiter-login"),
    path("admin/login/", AdminLoginView.as_view(), name="admin-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path(
        "password-reset/",
        PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password-reset/confirm/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
]
