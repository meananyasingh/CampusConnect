from rest_framework.permissions import BasePermission

from .models import User


class HasRole(BasePermission):
    required_role = None

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.role == self.required_role
        )


class IsStudent(HasRole):
    required_role = User.Role.STUDENT


class IsRecruiter(HasRole):
    required_role = User.Role.RECRUITER


class IsCollegeAdmin(HasRole):
    required_role = User.Role.ADMIN
