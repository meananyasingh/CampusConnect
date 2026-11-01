import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from colleges.models import AcademicProgram, College, CollegeAdminProfile
from notifications.models import Notification
from students.models import StudentProfile

from .models import StudentDocument


class StudentDocumentTests(APITestCase):
    password = "A-strong-test-password-2048"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_media = tempfile.TemporaryDirectory()
        cls.media_override = override_settings(MEDIA_ROOT=cls.temp_media.name)
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        cls.temp_media.cleanup()
        super().tearDownClass()

    def setUp(self):
        self.college = College.objects.create(name="Document College", code="DOC")
        self.other_college = College.objects.create(name="Other Document College", code="DOC2")
        self.program = AcademicProgram.objects.create(
            college=self.college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Computer Science",
        )
        self.other_program = AcademicProgram.objects.create(
            college=self.other_college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Electronics",
        )
        self.student = self.create_student(
            "document-student@example.com", self.college, self.program, "DOC001"
        )
        self.other_student = self.create_student(
            "other-document-student@example.com", self.other_college, self.other_program, "DOC002"
        )
        self.admin = self.create_admin("document-admin@example.com", self.college, "DOC-A")
        self.other_admin = self.create_admin(
            "other-document-admin@example.com", self.other_college, "DOC-B"
        )

    def create_student(self, email, college, program, enrollment):
        user = User.objects.create_user(
            email=email,
            password=self.password,
            role=User.Role.STUDENT,
            first_name="Document",
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

    def create_admin(self, email, college, employee_id):
        user = User.objects.create_user(
            email=email,
            password=self.password,
            role=User.Role.ADMIN,
            is_staff=True,
        )
        CollegeAdminProfile.objects.create(user=user, college=college, employee_id=employee_id)
        return user

    def upload(self, document_type="TENTH_MARKSHEET", filename="marksheet.pdf", content=b"%PDF-1.4 test"):
        self.client.force_authenticate(self.student)
        return self.client.post(
            reverse("student-document-list"),
            {
                "document_type": document_type,
                "title": "Academic marksheet",
                "academic_year": "2022-23",
                "student_note": "Clear scanned copy",
                "file": SimpleUploadedFile(filename, content, content_type="application/pdf"),
            },
            format="multipart",
        )

    def test_student_uploads_document_and_admin_is_notified(self):
        response = self.upload()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], StudentDocument.Status.PENDING)
        self.assertNotIn("file", response.data)
        self.assertTrue(Notification.objects.filter(recipient=self.admin).exists())

    def test_invalid_file_content_is_rejected(self):
        response = self.upload(content=b"not a real pdf")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_duplicate_pending_document_type_is_rejected(self):
        first = self.upload()
        second = self.upload(filename="second.pdf")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("document_type", second.data)

    def test_admin_sees_only_own_college_documents(self):
        own_document_id = self.upload().data["id"]
        StudentDocument.objects.create(
            student=self.other_student.student_profile,
            document_type=StudentDocument.DocumentType.COLLEGE_ID,
            title="Other college ID",
            file=SimpleUploadedFile("id.png", b"\x89PNG\r\n\x1a\nimage"),
            original_filename="id.png",
            file_size=13,
        )
        self.client.force_authenticate(self.admin)

        response = self.client.get(reverse("admin-document-list"))

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], own_document_id)

    def test_admin_verifies_pending_document_and_student_is_notified(self):
        document_id = self.upload().data["id"]
        self.client.force_authenticate(self.admin)

        response = self.client.patch(
            reverse("admin-document-review", args=(document_id,)),
            {"status": "VERIFIED", "review_note": "Details match college records."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], StudentDocument.Status.VERIFIED)
        self.assertTrue(Notification.objects.filter(recipient=self.student).exists())

    def test_rejection_requires_reason_and_allows_new_submission(self):
        document_id = self.upload().data["id"]
        self.client.force_authenticate(self.admin)
        invalid = self.client.patch(
            reverse("admin-document-review", args=(document_id,)),
            {"status": "REJECTED", "review_note": ""},
            format="json",
        )
        valid = self.client.patch(
            reverse("admin-document-review", args=(document_id,)),
            {"status": "REJECTED", "review_note": "The image is unreadable."},
            format="json",
        )
        resubmitted = self.upload(filename="clear-copy.pdf")

        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(valid.status_code, status.HTTP_200_OK)
        self.assertEqual(resubmitted.status_code, status.HTTP_201_CREATED)

    def test_other_college_admin_cannot_review_or_download_document(self):
        document_id = self.upload().data["id"]
        self.client.force_authenticate(self.other_admin)

        review = self.client.patch(
            reverse("admin-document-review", args=(document_id,)),
            {"status": "VERIFIED"},
            format="json",
        )
        download = self.client.get(reverse("admin-document-download", args=(document_id,)))

        self.assertEqual(review.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(download.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_can_download_own_document_but_not_another_students(self):
        own_id = self.upload().data["id"]
        other_document = StudentDocument.objects.create(
            student=self.other_student.student_profile,
            document_type=StudentDocument.DocumentType.COLLEGE_ID,
            title="Other ID",
            file=SimpleUploadedFile("other.pdf", b"%PDF-1.4 other"),
            original_filename="other.pdf",
            file_size=14,
        )
        self.client.force_authenticate(self.student)

        own = self.client.get(reverse("student-document-download", args=(own_id,)))
        other = self.client.get(reverse("student-document-download", args=(other_document.id,)))

        self.assertEqual(own.status_code, status.HTTP_200_OK)
        self.assertEqual(own["Content-Type"], "application/pdf")
        self.assertEqual(other.status_code, status.HTTP_404_NOT_FOUND)

    def test_verified_document_cannot_be_deleted(self):
        document_id = self.upload().data["id"]
        document = StudentDocument.objects.get(pk=document_id)
        document.status = StudentDocument.Status.VERIFIED
        document.save(update_fields=("status", "updated_at"))
        self.client.force_authenticate(self.student)

        response = self.client.delete(reverse("student-document-detail", args=(document_id,)))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(StudentDocument.objects.filter(pk=document_id).exists())

    def test_summary_tracks_required_document_readiness(self):
        document_id = self.upload().data["id"]
        document = StudentDocument.objects.get(pk=document_id)
        document.status = StudentDocument.Status.VERIFIED
        document.save(update_fields=("status", "updated_at"))
        self.client.force_authenticate(self.student)

        response = self.client.get(reverse("student-document-summary"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["verified_required"], 1)
        self.assertEqual(response.data["required_total"], 3)
        self.assertEqual(response.data["percentage"], 33)

