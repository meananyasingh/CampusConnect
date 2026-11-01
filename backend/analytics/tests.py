from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from applications.models import Application
from colleges.models import AcademicProgram, College, CollegeAdminProfile
from companies.models import Company, RecruiterProfile
from opportunities.models import Opportunity
from placements.models import PlacementRecord
from students.models import StudentProfile, StudentResume


class CollegeAnalyticsTests(APITestCase):
    def setUp(self):
        self.college = College.objects.create(name="Analytics College", code="ANC")
        self.other_college = College.objects.create(name="Private College", code="PVC")
        self.program = AcademicProgram.objects.create(
            college=self.college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Computer Science",
        )
        self.other_program = AcademicProgram.objects.create(
            college=self.other_college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Private Branch",
        )
        self.admin_user = User.objects.create_user(
            email="analytics-admin@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        CollegeAdminProfile.objects.create(
            user=self.admin_user,
            college=self.college,
            employee_id="ANC-ADMIN",
        )
        self.company = Company.objects.create(
            name="Analytics Employer",
            industry="Technology",
            website="https://analytics-employer.example.com",
            contact_email="hr@analytics-employer.example.com",
        )
        self.recruiter = User.objects.create_user(
            email="analytics-recruiter@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.RECRUITER,
        )
        RecruiterProfile.objects.create(user=self.recruiter, company=self.company, designation="Recruiter")
        self.student = self.create_student("analytics-student@example.com", self.college, self.program, "ANC001")
        self.other_student = self.create_student(
            "private-student@example.com", self.other_college, self.other_program, "PVC001"
        )
        self.application = self.create_application(self.student.student_profile, "Analytics Engineer")
        self.create_application(self.other_student.student_profile, "Private Engineer")
        PlacementRecord.objects.create(
            application=self.application,
            college=self.college,
            annual_package=Decimal("900000.00"),
            offer_date=timezone.localdate(),
            status=PlacementRecord.Status.ACCEPTED,
            verified_by=self.admin_user,
        )
        self.client.force_authenticate(self.admin_user)

    @staticmethod
    def create_student(email, college, program, enrollment):
        user = User.objects.create_user(
            email=email,
            password="A-strong-test-password-2048",
            role=User.Role.STUDENT,
        )
        StudentProfile.objects.create(
            user=user,
            college=college,
            program=program,
            enrollment_number=enrollment,
            graduation_year=2027,
            cgpa=Decimal("8.00"),
        )
        return user

    def create_application(self, student, title):
        resume = StudentResume.objects.bulk_create([
            StudentResume(
                student=student,
                title="Resume",
                file="students/resumes/analytics.pdf",
                original_filename="analytics.pdf",
                file_size=100,
                is_primary=True,
            )
        ])[0]
        opportunity = Opportunity.objects.create(
            company=self.company,
            created_by=self.recruiter,
            title=title,
            opportunity_type=Opportunity.Type.JOB,
            description="Analytics test opportunity.",
            location="Delhi",
            work_mode=Opportunity.WorkMode.HYBRID,
            application_deadline=timezone.localdate() + timedelta(days=10),
            status=Opportunity.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        opportunity.target_colleges.add(student.college)
        return Application.objects.create(
            opportunity=opportunity,
            student=student,
            resume=resume,
            status=Application.Status.SELECTED,
        )

    def test_overview_contains_scoped_pipeline_branch_and_company_data(self):
        response = self.client.get(reverse("college-analytics"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        selected = next(item for item in response.data["application_pipeline"] if item["name"] == "Selected")
        self.assertEqual(selected["count"], 1)
        self.assertEqual(len(response.data["branch_performance"]), 1)
        self.assertEqual(response.data["branch_performance"][0]["placed_students"], 1)
        self.assertEqual(response.data["company_placements"][0]["name"], self.company.name)

    def test_student_csv_is_downloadable_and_excludes_other_college(self):
        response = self.client.get(reverse("student-csv-report"))
        content = response.content.decode()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(self.student.email, content)
        self.assertNotIn(self.other_student.email, content)

    def test_application_and_placement_reports_are_downloadable(self):
        application_response = self.client.get(reverse("application-csv-report"))
        placement_response = self.client.get(reverse("placement-csv-report"))

        self.assertIn("Analytics Engineer", application_response.content.decode())
        self.assertNotIn("Private Engineer", application_response.content.decode())
        self.assertIn("900000.00", placement_response.content.decode())

    def test_college_admin_can_suspend_only_own_student_account(self):
        own_response = self.client.patch(
            reverse("college-student-detail", args=(self.student.student_profile.id,)),
            {"account_is_active": False},
            format="json",
        )
        other_response = self.client.patch(
            reverse("college-student-detail", args=(self.other_student.student_profile.id,)),
            {"account_is_active": False},
            format="json",
        )

        self.assertEqual(own_response.status_code, status.HTTP_200_OK)
        self.assertFalse(own_response.data["account_is_active"])
        self.assertEqual(other_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_dashboard_contains_only_the_students_activity(self):
        self.client.force_authenticate(self.student)

        response = self.client.get(reverse("student-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["stats"]["total_applications"], 1)
        self.assertEqual(len(response.data["recent_applications"]), 1)
        self.assertEqual(
            response.data["recent_applications"][0]["opportunity"]["title"],
            "Analytics Engineer",
        )

    def test_recruiter_dashboard_is_scoped_to_the_recruiters_company(self):
        self.client.force_authenticate(self.recruiter)

        response = self.client.get(reverse("recruiter-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["company"]["id"], self.company.id)
        self.assertEqual(response.data["stats"]["total_applications"], 2)
        self.assertEqual(len(response.data["opportunity_performance"]), 2)

    def test_dashboard_endpoints_enforce_their_roles(self):
        student_response = self.client.get(reverse("student-dashboard"))
        recruiter_response = self.client.get(reverse("recruiter-dashboard"))

        self.assertEqual(student_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(recruiter_response.status_code, status.HTTP_403_FORBIDDEN)
