from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from applications.models import Application
from colleges.models import AcademicProgram, College, CollegeAdminProfile
from companies.models import Company, CompanyCollegePartnership, RecruiterProfile
from opportunities.models import Opportunity
from students.models import StudentProfile, StudentResume

from .models import CollegePlacementPolicy, PlacementDrive, PlacementRecord


class PlacementTests(APITestCase):
    def setUp(self):
        self.college = College.objects.create(name="Placement College", code="PLC")
        self.other_college = College.objects.create(name="Other Placement College", code="OPC")
        self.program = AcademicProgram.objects.create(
            college=self.college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Computer Science",
        )
        self.other_program = AcademicProgram.objects.create(
            college=self.other_college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Information Technology",
        )
        self.admin_user = self.create_admin("placement-admin@example.com", self.college, "PLC-ADMIN")
        self.other_admin = self.create_admin("other-admin@example.com", self.other_college, "OPC-ADMIN")
        self.company = Company.objects.create(
            name="Placement Technologies",
            industry="Technology",
            website="https://placement.example.com",
            contact_email="hr@placement.example.com",
        )
        self.recruiter = User.objects.create_user(
            email="placement-recruiter@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.RECRUITER,
        )
        RecruiterProfile.objects.create(user=self.recruiter, company=self.company, designation="Recruiter")
        CompanyCollegePartnership.objects.create(
            company=self.company,
            college=self.college,
            status=CompanyCollegePartnership.Status.VERIFIED,
        )
        self.student = self.create_student(
            "placed-student@example.com", self.college, self.program, "PLC001"
        )
        self.resume = self.create_resume(self.student.student_profile)
        self.opportunity = self.create_opportunity(self.college)
        self.application = Application.objects.create(
            opportunity=self.opportunity,
            student=self.student.student_profile,
            resume=self.resume,
            status=Application.Status.SELECTED,
        )

    @staticmethod
    def create_admin(email, college, employee_id):
        user = User.objects.create_user(
            email=email,
            password="A-strong-test-password-2048",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        CollegeAdminProfile.objects.create(user=user, college=college, employee_id=employee_id)
        return user

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

    @staticmethod
    def create_resume(student):
        return StudentResume.objects.bulk_create([
            StudentResume(
                student=student,
                title="Placement resume",
                file="students/resumes/placement.pdf",
                original_filename="placement.pdf",
                file_size=100,
                is_primary=True,
            )
        ])[0]

    def create_opportunity(self, college):
        opportunity = Opportunity.objects.create(
            company=self.company,
            created_by=self.recruiter,
            title="Graduate Engineer",
            opportunity_type=Opportunity.Type.JOB,
            description="Graduate role.",
            location="Pune",
            work_mode=Opportunity.WorkMode.ONSITE,
            application_deadline=timezone.localdate() + timedelta(days=10),
            status=Opportunity.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        opportunity.target_colleges.add(college)
        return opportunity

    def create_record(self, **overrides):
        payload = {
            "application_id": self.application.id,
            "annual_package": "850000.00",
            "offer_date": str(timezone.localdate()),
            "joining_date": str(timezone.localdate() + timedelta(days=60)),
            "status": PlacementRecord.Status.OFFERED,
            "student_message": "Congratulations on your selection.",
            "admin_notes": "Offer verified with recruiter.",
        }
        payload.update(overrides)
        self.client.force_authenticate(self.admin_user)
        return self.client.post(reverse("college-placement-list"), payload, format="json")

    def test_admin_can_configure_their_college_placement_policy(self):
        self.client.force_authenticate(self.admin_user)

        initial = self.client.get(reverse("college-placement-policy"))
        response = self.client.patch(
            reverse("college-placement-policy"),
            {
                "require_verified_documents": True,
                "minimum_profile_completion": 70,
                "minimum_cgpa": "7.50",
                "max_active_backlogs": 1,
                "student_message": "Complete your college placement requirements.",
            },
            format="json",
        )

        self.assertEqual(initial.status_code, status.HTTP_200_OK)
        self.assertTrue(initial.data["applications_enabled"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["require_verified_documents"])
        self.assertEqual(response.data["minimum_profile_completion"], 70)
        self.assertEqual(Decimal(response.data["minimum_cgpa"]), Decimal("7.50"))
        policy = CollegePlacementPolicy.objects.get(college=self.college)
        self.assertEqual(policy.updated_by, self.admin_user)

    def test_each_admin_only_receives_their_own_college_policy(self):
        CollegePlacementPolicy.objects.create(
            college=self.college,
            applications_enabled=False,
            student_message="Applications are paused for Placement College.",
        )
        self.client.force_authenticate(self.other_admin)

        response = self.client.get(reverse("college-placement-policy"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["college"]["id"], self.other_college.id)
        self.assertTrue(response.data["applications_enabled"])

    def test_student_readiness_explains_every_college_policy_blocker(self):
        CollegePlacementPolicy.objects.create(
            college=self.college,
            applications_enabled=False,
            require_verified_documents=True,
            minimum_profile_completion=100,
            minimum_cgpa=Decimal("9.00"),
            max_active_backlogs=0,
            student_message="Placement applications are temporarily paused.",
        )
        self.student.student_profile.active_backlogs = 2
        self.student.student_profile.save(update_fields=("active_backlogs", "updated_at"))
        self.client.force_authenticate(self.student)

        response = self.client.get(reverse("student-placement-readiness"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_ready"])
        self.assertEqual(len(response.data["blockers"]), 5)
        self.assertIn("temporarily paused", response.data["blockers"][0])
        self.assertFalse(response.data["document_verification"]["is_complete"])
        self.assertEqual(response.data["policy"]["minimum_profile_completion"], 100)

    def test_college_admin_can_record_selected_student_placement(self):
        response = self.create_record()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["college_name"], self.college.name)
        self.assertEqual(response.data["application"]["student"]["id"], self.student.student_profile.id)

    def test_non_selected_application_cannot_be_recorded(self):
        self.application.status = Application.Status.SHORTLISTED
        self.application.save(update_fields=("status", "updated_at"))

        response = self.create_record()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("application_id", response.data)

    def test_other_college_admin_cannot_access_placement(self):
        placement_id = self.create_record().data["id"]
        self.client.force_authenticate(self.other_admin)

        response = self.client.get(reverse("college-placement-detail", args=(placement_id,)))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_can_accept_own_offer(self):
        placement_id = self.create_record().data["id"]
        self.client.force_authenticate(self.student)

        response = self.client.patch(
            reverse("student-placement-decision", args=(placement_id,)),
            {"status": PlacementRecord.Status.ACCEPTED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], PlacementRecord.Status.ACCEPTED)
        self.assertNotIn("admin_notes", response.data)

    def test_student_cannot_change_another_students_offer(self):
        placement_id = self.create_record().data["id"]
        other_student = self.create_student(
            "other-student@example.com", self.college, self.program, "PLC002"
        )
        self.client.force_authenticate(other_student)

        response = self.client.patch(
            reverse("student-placement-decision", args=(placement_id,)),
            {"status": PlacementRecord.Status.DECLINED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_mark_accepted_offer_as_joined(self):
        placement_id = self.create_record().data["id"]
        self.client.patch(
            reverse("college-placement-detail", args=(placement_id,)),
            {"status": PlacementRecord.Status.ACCEPTED},
            format="json",
        )

        response = self.client.patch(
            reverse("college-placement-detail", args=(placement_id,)),
            {"status": PlacementRecord.Status.JOINED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], PlacementRecord.Status.JOINED)

    def test_dashboard_is_scoped_and_calculates_placement_metrics(self):
        self.create_record()
        self.client.force_authenticate(self.admin_user)

        response = self.client.get(reverse("college-dashboard"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_students"], 1)
        self.assertEqual(response.data["verified_companies"], 1)
        self.assertEqual(response.data["total_applications"], 1)
        self.assertEqual(response.data["placed_students"], 1)
        self.assertEqual(response.data["placement_percentage"], 100.0)
        self.assertEqual(Decimal(response.data["highest_package"]), Decimal("850000.00"))

    def create_drive(self, **overrides):
        payload = {
            "title": "Annual Technology Drive",
            "description": "Coordinated hiring for graduating students.",
            "start_date": str(timezone.localdate() + timedelta(days=15)),
            "end_date": str(timezone.localdate() + timedelta(days=17)),
            "venue": "Main Auditorium",
            "status": PlacementDrive.Status.DRAFT,
            "opportunity_ids": [self.opportunity.id],
        }
        payload.update(overrides)
        self.client.force_authenticate(self.admin_user)
        return self.client.post(reverse("college-drive-list"), payload, format="json")

    def test_college_admin_can_create_and_monitor_a_drive(self):
        response = self.create_drive()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["college"]["id"], self.college.id)
        self.assertEqual(response.data["company_count"], 1)
        self.assertEqual(response.data["opportunity_count"], 1)
        self.assertEqual(response.data["application_count"], 1)
        self.assertEqual(response.data["selected_count"], 1)

    def test_admin_cannot_add_an_opportunity_from_another_college(self):
        private_opportunity = self.create_opportunity(self.other_college)

        response = self.create_drive(opportunity_ids=[private_opportunity.id])

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("opportunity_ids", response.data)

    def test_students_only_see_published_drives_for_their_college(self):
        drive_id = self.create_drive().data["id"]
        self.client.patch(
            reverse("college-drive-detail", args=(drive_id,)),
            {"status": PlacementDrive.Status.UPCOMING},
            format="json",
        )
        self.client.force_authenticate(self.student)

        response = self.client.get(reverse("student-drive-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], drive_id)

    def test_recruiter_sees_drive_containing_their_company_opportunity(self):
        drive_id = self.create_drive(status=PlacementDrive.Status.UPCOMING).data["id"]
        self.client.force_authenticate(self.recruiter)

        response = self.client.get(reverse("recruiter-drive-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [drive_id])

    def test_drive_status_must_follow_the_lifecycle(self):
        drive_id = self.create_drive().data["id"]

        response = self.client.patch(
            reverse("college-drive-detail", args=(drive_id,)),
            {"status": PlacementDrive.Status.COMPLETED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)
