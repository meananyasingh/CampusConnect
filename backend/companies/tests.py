from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from colleges.models import College, CollegeAdminProfile

from .models import Company, CompanyCollegePartnership, RecruiterProfile


class CompanyAccessTests(APITestCase):
    def setUp(self):
        self.college_a = College.objects.create(name="College A", code="CA-COMP")
        self.college_b = College.objects.create(name="College B", code="CB-COMP")
        self.company = Company.objects.create(
            name="Example Technologies",
            industry="Technology",
            website="https://example.com",
            contact_email="careers@example.com",
        )
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.RECRUITER,
        )
        RecruiterProfile.objects.create(
            user=self.owner,
            company=self.company,
            designation="HR Manager",
            is_company_owner=True,
        )
        self.partnership_a = CompanyCollegePartnership.objects.create(
            company=self.company,
            college=self.college_a,
        )
        self.partnership_b = CompanyCollegePartnership.objects.create(
            company=self.company,
            college=self.college_b,
        )

    def create_admin(self, email, college):
        user = User.objects.create_user(
            email=email,
            password="A-strong-test-password-2048",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        CollegeAdminProfile.objects.create(user=user, college=college, employee_id=email[:5])
        return user

    def test_recruiter_can_view_and_update_own_company(self):
        self.client.force_authenticate(self.owner)

        get_response = self.client.get(reverse("recruiter-company"))
        patch_response = self.client.patch(
            reverse("recruiter-company"),
            {"headquarters": "Bengaluru", "description": "Builds useful software."},
            format="json",
        )

        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["headquarters"], "Bengaluru")
        self.assertEqual(len(patch_response.data["partnerships"]), 2)

    def test_non_owner_recruiter_cannot_update_company(self):
        member = User.objects.create_user(
            email="member@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.RECRUITER,
        )
        RecruiterProfile.objects.create(
            user=member,
            company=self.company,
            designation="Recruiter",
            is_company_owner=False,
        )
        self.client.force_authenticate(member)

        response = self.client.patch(
            reverse("recruiter-company"),
            {"description": "Unauthorized change"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_identity_change_resets_company_verification(self):
        self.partnership_a.status = CompanyCollegePartnership.Status.VERIFIED
        self.partnership_a.save(update_fields=("status", "updated_at"))
        self.client.force_authenticate(self.owner)

        response = self.client.patch(
            reverse("recruiter-company"),
            {"website": "https://new-example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.partnership_a.refresh_from_db()
        self.assertEqual(self.partnership_a.status, CompanyCollegePartnership.Status.PENDING)

    def test_college_admin_sees_only_own_partnerships(self):
        admin = self.create_admin("admin-a@example.com", self.college_a)
        self.client.force_authenticate(admin)

        response = self.client.get(reverse("admin-company-partnership-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["college"]["id"], self.college_a.id)

    def test_college_admin_can_verify_only_own_partnership(self):
        admin = self.create_admin("admin-a@example.com", self.college_a)
        self.client.force_authenticate(admin)

        own_response = self.client.patch(
            reverse("admin-company-partnership-detail", args=(self.partnership_a.id,)),
            {"status": "VERIFIED", "review_note": "Company details checked."},
            format="json",
        )
        other_response = self.client.patch(
            reverse("admin-company-partnership-detail", args=(self.partnership_b.id,)),
            {"status": "VERIFIED"},
            format="json",
        )

        self.assertEqual(own_response.status_code, status.HTTP_200_OK)
        self.assertEqual(own_response.data["status"], "VERIFIED")
        self.assertIsNotNone(own_response.data["reviewed_at"])
        self.assertEqual(other_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_access_recruiter_company(self):
        student = User.objects.create_user(
            email="student-company@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.STUDENT,
        )
        self.client.force_authenticate(student)

        response = self.client.get(reverse("recruiter-company"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_recruiter_can_request_multiple_colleges_from_one_account(self):
        third_college = College.objects.create(name="College C", code="CC-COMP")
        new_company = Company.objects.create(
            name="One Account Company",
            industry="Technology",
            website="https://one-account.example.com",
            contact_email="hr@one-account.example.com",
        )
        recruiter = User.objects.create_user(
            email="multi-college@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.RECRUITER,
        )
        RecruiterProfile.objects.create(
            user=recruiter,
            company=new_company,
            designation="Recruiter",
            is_company_owner=True,
        )
        self.client.force_authenticate(recruiter)

        first = self.client.post(
            reverse("recruiter-partnership-list"),
            {"college_id": self.college_a.id},
            format="json",
        )
        second = self.client.post(
            reverse("recruiter-partnership-list"),
            {"college_id": third_college.id},
            format="json",
        )
        duplicate = self.client.post(
            reverse("recruiter-partnership-list"),
            {"college_id": self.college_a.id},
            format="json",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(new_company.college_partnerships.count(), 2)

    def test_recruiter_can_cancel_only_pending_request(self):
        self.client.force_authenticate(self.owner)

        pending_response = self.client.delete(
            reverse("recruiter-partnership-detail", args=(self.partnership_a.id,))
        )
        self.partnership_b.status = CompanyCollegePartnership.Status.VERIFIED
        self.partnership_b.save(update_fields=("status", "updated_at"))
        verified_response = self.client.delete(
            reverse("recruiter-partnership-detail", args=(self.partnership_b.id,))
        )

        self.assertEqual(pending_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(verified_response.status_code, status.HTTP_400_BAD_REQUEST)
