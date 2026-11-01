from datetime import date, timedelta
import re
from tempfile import TemporaryDirectory

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from colleges.models import AcademicProgram, College, CollegeAdminProfile

from .models import StudentImportBatch, StudentProfile, StudentProject, StudentResume


class StudentBulkImportTests(APITestCase):
    def setUp(self):
        self.college = College.objects.create(name="Import College", code="IMP")
        self.other_college = College.objects.create(name="Other Import College", code="OIC")
        self.program = AcademicProgram.objects.create(
            college=self.college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Computer Science",
        )
        self.admin = User.objects.create_user(
            email="import-admin@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        CollegeAdminProfile.objects.create(
            user=self.admin,
            college=self.college,
            employee_id="IMPORT-1",
        )
        self.other_admin = User.objects.create_user(
            email="other-import-admin@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        CollegeAdminProfile.objects.create(
            user=self.other_admin,
            college=self.other_college,
            employee_id="IMPORT-2",
        )
        self.client.force_authenticate(self.admin)

    def csv_file(self, rows):
        header = "email,first_name,last_name,enrollment_number,program_id,graduation_year,cgpa,active_backlogs\n"
        content = header + "\n".join(rows) + "\n"
        return SimpleUploadedFile("students.csv", content.encode(), content_type="text/csv")

    def test_admin_can_download_college_specific_template(self):
        response = self.client.get(reverse("college-student-import-template"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn(str(self.program.id), response.content.decode())

    def test_preview_reports_valid_and_invalid_rows_without_creating_accounts(self):
        upload = self.csv_file([
            f"new@example.com,New,Student,IMP001,{self.program.id},2028,8.5,0",
            f"invalid-email,Bad,Student,IMP002,{self.program.id},2028,12,0",
        ])

        response = self.client.post(reverse("college-student-import-list"), {"file": upload}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["valid_rows"], 1)
        self.assertEqual(response.data["invalid_rows"], 1)
        self.assertIn("email", response.data["rows"][1]["errors"])
        self.assertFalse(User.objects.filter(email="new@example.com").exists())

    def test_confirm_import_creates_only_valid_students_and_sends_activation(self):
        upload = self.csv_file([
            f"new@example.com,New,Student,IMP001,{self.program.id},2028,8.5,0",
            f"bad@example.com,Bad,Student,IMP002,99999,2028,8.0,0",
        ])
        preview = self.client.post(reverse("college-student-import-list"), {"file": upload}, format="multipart")

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("college-student-import-confirm", args=(preview.data["id"],)),
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["imported_count"], 1)
        user = User.objects.get(email="new@example.com")
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.student_profile.college, self.college)
        self.assertFalse(User.objects.filter(email="bad@example.com").exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/activate-account/", mail.outbox[0].body)
        uid, token = re.search(r"/activate-account/([^/]+)/([^/\s]+)", mail.outbox[0].body).groups()
        self.client.force_authenticate(user=None)
        activation = self.client.post(
            reverse("password-reset-confirm"),
            {
                "uid": uid,
                "token": token,
                "password": "A-new-private-password-4096",
                "password_confirm": "A-new-private-password-4096",
            },
            format="json",
        )
        self.assertEqual(activation.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("A-new-private-password-4096"))

    def test_import_cannot_be_confirmed_twice(self):
        upload = self.csv_file([
            f"once@example.com,One,Student,IMP003,{self.program.id},2028,,0",
        ])
        preview = self.client.post(reverse("college-student-import-list"), {"file": upload}, format="multipart")
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("college-student-import-confirm", args=(preview.data["id"],)))

        response = self.client.post(reverse("college-student-import-confirm", args=(preview.data["id"],)))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.filter(email="once@example.com").count(), 1)

    def test_other_college_admin_cannot_confirm_batch(self):
        upload = self.csv_file([
            f"scoped@example.com,Scoped,Student,IMP004,{self.program.id},2028,,0",
        ])
        preview = self.client.post(reverse("college-student-import-list"), {"file": upload}, format="multipart")
        self.client.force_authenticate(self.other_admin)

        response = self.client.post(reverse("college-student-import-confirm", args=(preview.data["id"],)))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(User.objects.filter(email="scoped@example.com").exists())

    def test_admin_can_resend_pending_activation_with_cooldown(self):
        pending_user = User(
            email="pending-activation@example.com",
            first_name="Pending",
            last_name="Student",
            role=User.Role.STUDENT,
        )
        pending_user.set_unusable_password()
        pending_user.save()
        profile = StudentProfile.objects.create(
            user=pending_user,
            college=self.college,
            program=self.program,
            enrollment_number="IMP009",
            graduation_year=2028,
        )

        response = self.client.post(reverse("college-student-resend-activation", args=(profile.id,)))
        repeated = self.client.post(reverse("college-student-resend-activation", args=(profile.id,)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["activation_status"], "PENDING")
        self.assertEqual(response.data["activation_email_count"], 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(repeated.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_college_cannot_resend_student_activation(self):
        pending_user = User(email="private-pending@example.com", role=User.Role.STUDENT)
        pending_user.set_unusable_password()
        pending_user.save()
        profile = StudentProfile.objects.create(
            user=pending_user,
            college=self.college,
            program=self.program,
            enrollment_number="IMP010",
            graduation_year=2028,
        )
        self.client.force_authenticate(self.other_admin)

        response = self.client.post(reverse("college-student-resend-activation", args=(profile.id,)))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(len(mail.outbox), 0)


class StudentProfileTests(APITestCase):
    def setUp(self):
        self.college_a = College.objects.create(name="College A", code="CA")
        self.college_b = College.objects.create(name="College B", code="CB")
        self.program_a = AcademicProgram.objects.create(
            college=self.college_a,
            degree=AcademicProgram.Degree.BTECH,
            branch="Computer Science",
        )
        self.program_b = AcademicProgram.objects.create(
            college=self.college_b,
            degree=AcademicProgram.Degree.BTECH,
            branch="Information Technology",
        )
        self.student_a = self.create_student("student-a@example.com", self.college_a, self.program_a, "CA001")
        self.student_b = self.create_student("student-b@example.com", self.college_b, self.program_b, "CB001")

    @staticmethod
    def create_student(email, college, program, enrollment_number):
        user = User.objects.create_user(
            email=email,
            password="A-strong-test-password-2048",
            role=User.Role.STUDENT,
        )
        StudentProfile.objects.create(
            user=user,
            college=college,
            program=program,
            enrollment_number=enrollment_number,
            graduation_year=2027,
        )
        return user

    def test_student_can_view_only_own_profile_endpoint(self):
        self.client.force_authenticate(self.student_a)

        response = self.client.get(reverse("student-profile"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["email"], self.student_a.email)

    def test_student_cannot_access_college_student_list(self):
        self.client.force_authenticate(self.student_a)

        response = self.client.get(reverse("college-student-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_college_admin_sees_only_students_from_own_college(self):
        admin = User.objects.create_user(
            email="officer@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        CollegeAdminProfile.objects.create(
            user=admin,
            college=self.college_a,
            employee_id="PO001",
        )
        self.client.force_authenticate(admin)

        response = self.client.get(reverse("college-student-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        emails = [student["user"]["email"] for student in response.data["results"]]
        self.assertEqual(emails, [self.student_a.email])

    def test_profile_rejects_program_from_another_college(self):
        profile = self.student_a.student_profile
        profile.program = self.program_b

        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_student_can_update_personal_and_academic_details(self):
        self.client.force_authenticate(self.student_a)

        response = self.client.patch(
            reverse("student-profile"),
            {
                "first_name": "Updated",
                "last_name": "Student",
                "phone": "+919876543210",
                "location": "Punjab",
                "career_objective": "Build useful software for real users.",
                "cgpa": "8.75",
                "tenth_percentage": "91.20",
                "twelfth_percentage": "88.40",
                "active_backlogs": 0,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_a.refresh_from_db()
        self.student_a.student_profile.refresh_from_db()
        self.assertEqual(self.student_a.first_name, "Updated")
        self.assertEqual(str(self.student_a.student_profile.cgpa), "8.75")

    def test_profile_rejects_out_of_range_cgpa(self):
        self.client.force_authenticate(self.student_a)

        response = self.client.patch(
            reverse("student-profile"),
            {"cgpa": "10.50"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cgpa", response.data)

    def test_profile_rejects_future_date_of_birth(self):
        self.client.force_authenticate(self.student_a)

        response = self.client.patch(
            reverse("student-profile"),
            {"date_of_birth": date.today() + timedelta(days=1)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("date_of_birth", response.data)

    def test_student_cannot_change_protected_enrollment_fields(self):
        self.client.force_authenticate(self.student_a)

        response = self.client.patch(
            reverse("student-profile"),
            {
                "enrollment_number": "CHANGED",
                "graduation_year": 2035,
                "college": self.college_b.id,
                "program": self.program_b.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student_a.student_profile.refresh_from_db()
        self.assertEqual(self.student_a.student_profile.enrollment_number, "CA001")
        self.assertEqual(self.student_a.student_profile.graduation_year, 2027)
        self.assertEqual(self.student_a.student_profile.college, self.college_a)

    def test_profile_picture_must_be_an_actual_image(self):
        self.client.force_authenticate(self.student_a)
        fake_image = SimpleUploadedFile(
            "profile.png",
            b"this is not image data",
            content_type="image/png",
        )

        response = self.client.patch(
            reverse("student-profile"),
            {"profile_picture": fake_image},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("profile_picture", response.data)


class StudentPortfolioTests(APITestCase):
    def setUp(self):
        college = College.objects.create(name="Portfolio College", code="PC")
        program = AcademicProgram.objects.create(
            college=college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Computer Science",
        )
        self.student = self.create_student("portfolio@example.com", college, program, "PC001")
        self.other_student = self.create_student("other@example.com", college, program, "PC002")
        self.client.force_authenticate(self.student)

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
        )
        return user

    def test_student_can_create_update_and_delete_own_skill(self):
        create_response = self.client.post(
            reverse("student-skill-list"),
            {
                "skill_name": "Django",
                "proficiency": "ADVANCED",
                "years_experience": "2.5",
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        skill_id = create_response.data["id"]
        update_response = self.client.patch(
            reverse("student-skill-detail", args=(skill_id,)),
            {"proficiency": "EXPERT"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["proficiency_display"], "Expert")

        delete_response = self.client.delete(reverse("student-skill-detail", args=(skill_id,)))
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_duplicate_skill_is_rejected_case_insensitively(self):
        self.client.post(
            reverse("student-skill-list"),
            {"skill_name": "React", "proficiency": "INTERMEDIATE"},
            format="json",
        )

        response = self.client.post(
            reverse("student-skill-list"),
            {"skill_name": "react", "proficiency": "ADVANCED"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("skill_name", response.data)

    def test_student_cannot_access_another_students_project(self):
        project = StudentProject.objects.create(
            student=self.other_student.student_profile,
            title="Private project",
            description="This belongs to another student.",
            start_date=date(2026, 1, 1),
        )

        response = self.client.get(reverse("student-project-detail", args=(project.id,)))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_project_rejects_end_date_before_start_date(self):
        response = self.client.post(
            reverse("student-project-list"),
            {
                "title": "CampusConnect",
                "description": "Placement management platform.",
                "start_date": "2026-06-01",
                "end_date": "2026-05-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_date", response.data)

    def test_ongoing_project_rejects_end_date(self):
        response = self.client.post(
            reverse("student-project-list"),
            {
                "title": "CampusConnect",
                "description": "Placement management platform.",
                "start_date": "2026-06-01",
                "end_date": "2026-07-01",
                "is_ongoing": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("end_date", response.data)

    def test_student_can_manage_certification(self):
        create_response = self.client.post(
            reverse("student-certification-list"),
            {
                "name": "Django Web Development",
                "issuing_organization": "Example Academy",
                "issue_date": "2026-01-10",
                "credential_url": "https://example.com/certificate/123",
            },
            format="json",
        )

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        list_response = self.client.get(reverse("student-certification-list"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)

    def test_certification_rejects_expiry_before_issue_date(self):
        response = self.client.post(
            reverse("student-certification-list"),
            {
                "name": "Invalid certificate",
                "issuing_organization": "Example Academy",
                "issue_date": "2026-03-01",
                "expiry_date": "2026-02-01",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expiry_date", response.data)

    def test_student_can_manage_experience(self):
        response = self.client.post(
            reverse("student-experience-list"),
            {
                "organization": "Acme Labs",
                "role": "Backend Intern",
                "employment_type": "INTERNSHIP",
                "start_date": "2026-01-01",
                "is_current": True,
                "description": "Built Django REST APIs.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["employment_type_display"], "Internship")

    def test_non_student_cannot_access_portfolio_api(self):
        recruiter = User.objects.create_user(
            email="recruiter@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.RECRUITER,
        )
        self.client.force_authenticate(recruiter)

        response = self.client.get(reverse("student-skill-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StudentResumeTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        cls.media_directory = TemporaryDirectory()
        cls.settings_override = override_settings(MEDIA_ROOT=cls.media_directory.name)
        cls.settings_override.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.settings_override.disable()
        cls.media_directory.cleanup()

    def setUp(self):
        college = College.objects.create(name="Resume College", code="RC")
        program = AcademicProgram.objects.create(
            college=college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Computer Science",
        )
        self.student = self.create_student("resume@example.com", college, program, "RC001")
        self.other_student = self.create_student("resume-other@example.com", college, program, "RC002")
        self.client.force_authenticate(self.student)

    @staticmethod
    def create_student(email, college, program, enrollment):
        user = User.objects.create_user(
            email=email,
            password="A-strong-test-password-2048",
            role=User.Role.STUDENT,
            first_name="Resume",
            last_name="Student",
        )
        StudentProfile.objects.create(
            user=user,
            college=college,
            program=program,
            enrollment_number=enrollment,
            graduation_year=2027,
        )
        return user

    @staticmethod
    def pdf(name="resume.pdf"):
        return SimpleUploadedFile(
            name,
            b"%PDF-1.4\nCampusConnect test resume",
            content_type="application/pdf",
        )

    def upload_resume(self, title, primary=False):
        return self.client.post(
            reverse("student-resume-list"),
            {"title": title, "file": self.pdf(), "is_primary": primary},
            format="multipart",
        )

    def test_first_resume_automatically_becomes_primary(self):
        response = self.upload_resume("Placement resume")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_primary"])
        self.assertEqual(response.data["original_filename"], "resume.pdf")

    def test_selecting_new_primary_unsets_previous_resume(self):
        first = self.upload_resume("General resume").data
        second = self.upload_resume("Backend resume").data

        response = self.client.patch(
            reverse("student-resume-detail", args=(second["id"],)),
            {"is_primary": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_primary"])
        self.assertFalse(StudentResume.objects.get(pk=first["id"]).is_primary)

    def test_primary_resume_cannot_be_directly_unset(self):
        resume = self.upload_resume("Primary resume").data

        response = self.client.patch(
            reverse("student-resume-detail", args=(resume["id"],)),
            {"is_primary": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("is_primary", response.data)

    def test_deleting_primary_promotes_remaining_resume(self):
        first = self.upload_resume("First resume").data
        second = self.upload_resume("Second resume").data

        response = self.client.delete(reverse("student-resume-detail", args=(first["id"],)))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(StudentResume.objects.get(pk=second["id"]).is_primary)

    def test_fake_pdf_is_rejected(self):
        response = self.client.post(
            reverse("student-resume-list"),
            {
                "title": "Unsafe file",
                "file": SimpleUploadedFile("resume.pdf", b"not a pdf", content_type="application/pdf"),
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_student_cannot_access_another_students_resume(self):
        other_resume = StudentResume.objects.create(
            student=self.other_student.student_profile,
            title="Private resume",
            file=self.pdf("private.pdf"),
            original_filename="private.pdf",
            file_size=32,
            is_primary=True,
        )

        response = self.client.get(reverse("student-resume-detail", args=(other_resume.id,)))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_primary_resume_increases_completion_score(self):
        before = self.client.get(reverse("student-profile-completion"))
        self.upload_resume("Placement resume")
        after = self.client.get(reverse("student-profile-completion"))

        self.assertEqual(before.status_code, status.HTTP_200_OK)
        self.assertEqual(after.status_code, status.HTTP_200_OK)
        self.assertEqual(after.data["percentage"], before.data["percentage"] + 10)
        self.assertEqual(len(after.data["sections"]), 8)
