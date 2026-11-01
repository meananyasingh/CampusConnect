from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from colleges.models import AcademicProgram, College, CollegeAdminProfile
from companies.models import Company, CompanyCollegePartnership, RecruiterProfile
from students.models import StudentProfile

from .models import Announcement, AnnouncementRead


class AnnouncementTests(APITestCase):
    def setUp(self):
        self.college = College.objects.create(name="Notice College", code="NTC")
        self.other_college = College.objects.create(name="Other Notice College", code="ONC")
        self.program = AcademicProgram.objects.create(college=self.college, degree=AcademicProgram.Degree.BTECH, branch="Computer Science")
        self.other_program = AcademicProgram.objects.create(college=self.college, degree=AcademicProgram.Degree.MBA, branch="Management")
        self.admin = self.create_admin("notice-admin@example.com", self.college, "NTC-A1")
        self.other_admin = self.create_admin("other-notice-admin@example.com", self.other_college, "ONC-A1")
        self.student = self.create_student("notice-student@example.com", self.program, 2027, "NTC001")
        self.other_student = self.create_student("mba-student@example.com", self.other_program, 2028, "NTC002")
        self.company = Company.objects.create(name="Notice Employer", industry="Technology", website="https://notice.example.com", contact_email="hr@notice.example.com")
        self.recruiter = User.objects.create_user(email="notice-recruiter@example.com", password="Strong-test-password-2048", role=User.Role.RECRUITER)
        RecruiterProfile.objects.create(user=self.recruiter, company=self.company, designation="Recruiter")
        CompanyCollegePartnership.objects.create(company=self.company, college=self.college, status=CompanyCollegePartnership.Status.VERIFIED)

    @staticmethod
    def create_admin(email, college, employee_id):
        user = User.objects.create_user(email=email, password="Strong-test-password-2048", role=User.Role.ADMIN, is_staff=True)
        CollegeAdminProfile.objects.create(user=user, college=college, employee_id=employee_id)
        return user

    def create_student(self, email, program, year, enrollment):
        user = User.objects.create_user(email=email, password="Strong-test-password-2048", role=User.Role.STUDENT)
        StudentProfile.objects.create(user=user, college=self.college, program=program, enrollment_number=enrollment, graduation_year=year)
        return user

    def payload(self, **overrides):
        values = {
            "title": "Aptitude test schedule",
            "body": "The aptitude assessment begins at 10 AM in Lab 2.",
            "announcement_type": Announcement.Type.ASSESSMENT,
            "priority": Announcement.Priority.IMPORTANT,
            "target_program_ids": [self.program.id],
            "target_graduation_years": [2027],
            "publish_at": (timezone.now() - timedelta(minutes=1)).isoformat(),
            "expires_at": (timezone.now() + timedelta(days=3)).isoformat(),
            "is_pinned": True,
        }
        values.update(overrides)
        return values

    def test_admin_notice_is_approved_and_only_visible_to_target_students(self):
        self.client.force_authenticate(self.admin)
        created = self.client.post(reverse("admin-announcement-list"), self.payload(), format="json")

        self.client.force_authenticate(self.student)
        target_response = self.client.get(reverse("student-announcement-list"))
        self.client.force_authenticate(self.other_student)
        other_response = self.client.get(reverse("student-announcement-list"))

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(created.data["approval_status"], Announcement.ApprovalStatus.APPROVED)
        self.assertEqual(len(target_response.data), 1)
        self.assertEqual(len(other_response.data), 0)

    def test_recruiter_notice_requires_college_approval(self):
        self.client.force_authenticate(self.recruiter)
        created = self.client.post(reverse("recruiter-announcement-list"), self.payload(college_id=self.college.id), format="json")
        self.client.force_authenticate(self.student)
        before_review = self.client.get(reverse("student-announcement-list"))
        self.client.force_authenticate(self.admin)
        reviewed = self.client.post(reverse("admin-announcement-review", args=(created.data["id"],)), {"approval_status": "APPROVED"}, format="json")
        self.client.force_authenticate(self.student)
        after_review = self.client.get(reverse("student-announcement-list"))

        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(before_review.data), 0)
        self.assertEqual(reviewed.status_code, status.HTTP_200_OK)
        self.assertEqual(len(after_review.data), 1)

    def test_recruiter_cannot_submit_to_unverified_college(self):
        self.client.force_authenticate(self.recruiter)
        response = self.client.post(reverse("recruiter-announcement-list"), self.payload(college_id=self.other_college.id), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("college_id", response.data)

    def test_student_can_mark_visible_announcement_as_read(self):
        self.client.force_authenticate(self.admin)
        announcement_id = self.client.post(reverse("admin-announcement-list"), self.payload(), format="json").data["id"]
        self.client.force_authenticate(self.student)
        response = self.client.post(reverse("student-announcement-read", args=(announcement_id,)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_read"])
        self.assertTrue(AnnouncementRead.objects.filter(announcement_id=announcement_id, user=self.student).exists())

    def test_other_college_admin_cannot_review_announcement(self):
        self.client.force_authenticate(self.recruiter)
        announcement_id = self.client.post(reverse("recruiter-announcement-list"), self.payload(college_id=self.college.id), format="json").data["id"]
        self.client.force_authenticate(self.other_admin)
        response = self.client.post(reverse("admin-announcement-review", args=(announcement_id,)), {"approval_status": "REJECTED"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
