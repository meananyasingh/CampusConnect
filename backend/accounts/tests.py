from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from colleges.models import AcademicProgram, College
from students.models import StudentProfile

from .models import User


class UserManagerTests(APITestCase):
    def test_create_user_uses_email_as_login_identifier(self):
        user = User.objects.create_user(
            email="Student@Example.COM",
            password="temporary-test-password",
            role=User.Role.STUDENT,
        )

        self.assertEqual(user.email, "student@example.com")
        self.assertTrue(user.check_password("temporary-test-password"))
        self.assertEqual(user.role, User.Role.STUDENT)

    def test_create_superuser_assigns_admin_role(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="temporary-test-password",
        )

        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)


class RegistrationTests(APITestCase):
    def setUp(self):
        self.college = College.objects.create(name="Example College", code="EC")
        self.program = AcademicProgram.objects.create(
            college=self.college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Computer Science and Engineering",
        )
        self.payload = {
            "email": "student@example.com",
            "first_name": "Campus",
            "last_name": "Student",
            "password": "A-strong-test-password-2048",
            "password_confirm": "A-strong-test-password-2048",
            "college": self.college.id,
            "program": self.program.id,
            "enrollment_number": "ec/2026/001",
            "graduation_year": 2027,
        }

    def test_student_registration_assigns_student_role(self):
        response = self.client.post(reverse("student-register"), self.payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], User.Role.STUDENT)
        self.assertNotIn("password", response.data)
        profile = StudentProfile.objects.get(user__email="student@example.com")
        self.assertEqual(profile.college, self.college)
        self.assertEqual(profile.program, self.program)
        self.assertEqual(profile.enrollment_number, "EC/2026/001")

    def test_recruiter_registration_assigns_recruiter_role(self):
        recruiter_payload = {
            key: value
            for key, value in self.payload.items()
            if key
            in {"email", "first_name", "last_name", "password", "password_confirm"}
        }
        recruiter_payload.update(
            {
                "company_name": "Campus Careers Pvt Ltd",
                "company_industry": "Technology",
                "company_website": "https://campus-careers.example.com",
                "company_email": "hr@campus-careers.example.com",
                "designation": "Talent Acquisition Lead",
                "phone": "+919876543210",
            }
        )
        response = self.client.post(reverse("recruiter-register"), recruiter_payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], User.Role.RECRUITER)
        self.assertEqual(response.data["email"], "student@example.com")
        recruiter = User.objects.get(pk=response.data["id"])
        self.assertEqual(recruiter.recruiter_profile.company.name, "Campus Careers Pvt Ltd")
        self.assertFalse(recruiter.recruiter_profile.company.college_partnerships.exists())

    def test_duplicate_email_is_rejected_case_insensitively(self):
        self.client.post(reverse("student-register"), self.payload)
        duplicate = {**self.payload, "email": "STUDENT@example.com"}

        response = self.client.post(reverse("student-register"), duplicate)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_confirmation_must_match(self):
        payload = {**self.payload, "password_confirm": "different-password"}

        response = self.client.post(reverse("student-register"), payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_student_program_must_belong_to_selected_college(self):
        other_college = College.objects.create(name="Other College", code="OC")
        other_program = AcademicProgram.objects.create(
            college=other_college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Information Technology",
        )
        payload = {**self.payload, "program": other_program.id}

        response = self.client.post(reverse("student-register"), payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("program", response.data)


class AuthenticationTests(APITestCase):
    password = "A-strong-test-password-2048"

    def setUp(self):
        self.student = User.objects.create_user(
            email="student@example.com",
            password=self.password,
            role=User.Role.STUDENT,
            first_name="Campus",
            last_name="Student",
        )

    def test_student_can_login_to_student_portal(self):
        response = self.client.post(
            reverse("student-login"),
            {"email": self.student.email, "password": self.password},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], User.Role.STUDENT)

    def test_student_cannot_login_to_recruiter_portal(self):
        response = self.client.post(
            reverse("recruiter-login"),
            {"email": self.student.email, "password": self.password},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_superuser_can_login_to_admin_portal(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password=self.password,
        )

        response = self.client.post(
            reverse("admin-login"),
            {"email": admin.email, "password": self.password},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["role"], User.Role.ADMIN)

    def test_authenticated_user_can_read_own_identity(self):
        login = self.client.post(
            reverse("student-login"),
            {"email": self.student.email, "password": self.password},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        response = self.client.get(reverse("current-user"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.student.email)

    def test_logout_blacklists_refresh_token(self):
        login = self.client.post(
            reverse("student-login"),
            {"email": self.student.email, "password": self.password},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

        logout = self.client.post(
            reverse("logout"),
            {"refresh": login.data["refresh"]},
        )

        self.assertEqual(logout.status_code, status.HTTP_204_NO_CONTENT)
        refresh = self.client.post(
            reverse("token-refresh"),
            {"refresh": login.data["refresh"]},
        )
        self.assertEqual(refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_current_user_endpoint_rejects_anonymous_request(self):
        response = self.client.get(reverse("current-user"))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PasswordResetTests(APITestCase):
    old_password = "A-strong-old-password-2048"
    new_password = "A-strong-new-password-4096"

    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.com",
            password=self.old_password,
            role=User.Role.STUDENT,
            first_name="Campus",
            last_name="Student",
        )

    def test_reset_request_sends_email_for_existing_account(self):
        response = self.client.post(
            reverse("password-reset-request"),
            {"email": self.user.email},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/reset-password/", mail.outbox[0].body)

    def test_reset_request_does_not_reveal_missing_account(self):
        response = self.client.post(
            reverse("password-reset-request"),
            {"email": "missing@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_valid_token_changes_password_and_invalidates_refresh_token(self):
        login = self.client.post(
            reverse("student-login"),
            {"email": self.user.email, "password": self.old_password},
        )
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        response = self.client.post(
            reverse("password-reset-confirm"),
            {
                "uid": uid,
                "token": token,
                "password": self.new_password,
                "password_confirm": self.new_password,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))
        refresh = self.client.post(
            reverse("token-refresh"),
            {"refresh": login.data["refresh"]},
        )
        self.assertEqual(refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_reset_token_is_rejected(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))

        response = self.client.post(
            reverse("password-reset-confirm"),
            {
                "uid": uid,
                "token": "invalid-token",
                "password": self.new_password,
                "password_confirm": self.new_password,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
