from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from colleges.models import AcademicProgram, College, CollegeAdminProfile
from students.models import StudentProfile

from .models import AuditEvent


class AuditEventTests(APITestCase):
    def setUp(self):
        self.college = College.objects.create(name="Audit College", code="AUD")
        self.other_college = College.objects.create(name="Other Audit College", code="OAU")
        self.program = AcademicProgram.objects.create(
            college=self.college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Computer Science",
        )
        self.admin = User.objects.create_user(
            email="audit-admin@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        CollegeAdminProfile.objects.create(
            user=self.admin,
            college=self.college,
            employee_id="AUD-1",
        )
        student_user = User.objects.create_user(
            email="audit-student@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.STUDENT,
        )
        self.student = StudentProfile.objects.create(
            user=student_user,
            college=self.college,
            program=self.program,
            enrollment_number="AUD001",
            graduation_year=2028,
        )
        self.client.force_authenticate(self.admin)

    def test_successful_authenticated_write_creates_college_scoped_event(self):
        response = self.client.patch(
            reverse("college-student-detail", args=(self.student.id,)),
            {"account_is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event = AuditEvent.objects.get()
        self.assertEqual(event.actor, self.admin)
        self.assertEqual(event.college, self.college)
        self.assertEqual(event.category, AuditEvent.Category.ACCOUNT)
        self.assertEqual(event.changed_fields, ["account_is_active"])

    def test_failed_write_is_not_logged(self):
        response = self.client.patch(
            reverse("college-student-detail", args=(999999,)),
            {"account_is_active": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(AuditEvent.objects.exists())

    def test_admin_only_lists_their_college_events_with_filters(self):
        AuditEvent.objects.create(
            actor=self.admin, actor_email=self.admin.email, actor_role=self.admin.role,
            college=self.college, category=AuditEvent.Category.DOCUMENT,
            action="Document Review", description="Verified marksheet",
            endpoint="/api/documents/admin/1/", http_method="PATCH",
        )
        AuditEvent.objects.create(
            actor_email="other@example.com", actor_role=User.Role.ADMIN,
            college=self.other_college, category=AuditEvent.Category.COMPANY,
            action="Company Review", description="Approved company",
            endpoint="/api/companies/admin/1/", http_method="PATCH",
        )

        response = self.client.get(reverse("audit-event-list"), {"category": "DOCUMENT"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["description"], "Verified marksheet")

    def test_admin_can_export_scoped_audit_csv(self):
        AuditEvent.objects.create(
            actor=self.admin, actor_email=self.admin.email, actor_role=self.admin.role,
            college=self.college, category=AuditEvent.Category.PLACEMENT,
            action="Policy Update", description="Changed placement policy",
            endpoint="/api/placements/admin/policy/", http_method="PATCH",
            changed_fields=["minimum_cgpa"],
        )

        response = self.client.get(reverse("audit-event-export"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("Policy Update", response.content.decode())
