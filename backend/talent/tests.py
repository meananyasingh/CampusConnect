from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from colleges.models import AcademicProgram, College
from companies.models import Company, CompanyCollegePartnership, RecruiterProfile
from students.models import Skill, StudentProfile, StudentResume, StudentSkill

from .models import TalentPool, TalentPoolMember


class RecruiterTalentTests(APITestCase):
    password = "A-strong-test-password-2048"

    def setUp(self):
        self.college_a = College.objects.create(name="College A", code="TAL-A")
        self.college_b = College.objects.create(name="College B", code="TAL-B")
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
        self.company = Company.objects.create(
            name="Talent Company",
            industry="Technology",
            website="https://talent.example.com",
            contact_email="careers@talent.example.com",
        )
        self.recruiter = self.create_recruiter("recruiter@talent.example.com", self.company)
        self.visible_student = self.create_student(
            "visible@example.com", self.college_a, self.program_a, "A001", cgpa=8.5
        )
        self.hidden_student = self.create_student(
            "hidden@example.com", self.college_a, self.program_a, "A002",
            is_visible_to_recruiters=False,
        )
        self.other_college_student = self.create_student(
            "other@example.com", self.college_b, self.program_b, "B001"
        )
        CompanyCollegePartnership.objects.create(
            company=self.company,
            college=self.college_a,
            status=CompanyCollegePartnership.Status.VERIFIED,
        )
        CompanyCollegePartnership.objects.create(
            company=self.company,
            college=self.college_b,
            status=CompanyCollegePartnership.Status.PENDING,
        )
        python = Skill.objects.create(name="Python")
        StudentSkill.objects.create(
            student=self.visible_student,
            skill=python,
            proficiency=StudentSkill.Proficiency.ADVANCED,
        )
        self.client.force_authenticate(self.recruiter)

    def create_recruiter(self, email, company):
        user = User.objects.create_user(
            email=email,
            password=self.password,
            role=User.Role.RECRUITER,
        )
        RecruiterProfile.objects.create(
            user=user,
            company=company,
            designation="Recruiter",
        )
        return user

    def create_student(self, email, college, program, enrollment, **profile_fields):
        user = User.objects.create_user(
            email=email,
            password=self.password,
            role=User.Role.STUDENT,
            first_name=email.split("@")[0].title(),
            last_name="Student",
        )
        return StudentProfile.objects.create(
            user=user,
            college=college,
            program=program,
            enrollment_number=enrollment,
            graduation_year=2027,
            **profile_fields,
        )

    def test_candidate_list_only_exposes_visible_students_from_verified_colleges(self):
        response = self.client.get(reverse("talent-candidate-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.visible_student.id)

    def test_candidate_filters_by_skill_and_cgpa(self):
        matched = self.client.get(reverse("talent-candidate-list"), {"skill": "python", "min_cgpa": 8})
        excluded = self.client.get(reverse("talent-candidate-list"), {"skill": "java"})

        self.assertEqual(matched.data["count"], 1)
        self.assertEqual(excluded.data["count"], 0)

    def test_recruiter_cannot_open_hidden_or_unverified_college_student(self):
        hidden = self.client.get(reverse("talent-candidate-detail", args=(self.hidden_student.id,)))
        unverified = self.client.get(
            reverse("talent-candidate-detail", args=(self.other_college_student.id,))
        )

        self.assertEqual(hidden.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(unverified.status_code, status.HTTP_404_NOT_FOUND)

    def test_authorized_resume_download_is_protected_by_candidate_scope(self):
        pdf = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        StudentResume.objects.create(
            student=self.visible_student,
            title="Primary resume",
            file=pdf,
            original_filename="resume.pdf",
            file_size=len(pdf.read()),
            is_primary=True,
        )
        response = self.client.get(
            reverse("talent-candidate-resume", args=(self.visible_student.id,))
        )
        hidden_response = self.client.get(
            reverse("talent-candidate-resume", args=(self.hidden_student.id,))
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(hidden_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_company_recruiters_share_their_company_pools(self):
        create = self.client.post(
            reverse("talent-pool-list"),
            {"name": "Backend shortlist", "description": "Strong Python candidates"},
            format="json",
        )
        second_recruiter = self.create_recruiter("second@talent.example.com", self.company)
        self.client.force_authenticate(second_recruiter)
        response = self.client.get(reverse("talent-pool-list"))

        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Backend shortlist")

    def test_recruiter_can_add_note_update_and_remove_candidate(self):
        pool = TalentPool.objects.create(
            company=self.company,
            created_by=self.recruiter,
            name="Interview later",
        )
        added = self.client.post(
            reverse("talent-pool-member-create", args=(pool.id,)),
            {"student_id": self.visible_student.id, "private_notes": "Strong projects"},
            format="json",
        )
        member_id = added.data["id"]
        updated = self.client.patch(
            reverse("talent-pool-member-detail", args=(pool.id, member_id)),
            {"private_notes": "Call next week"},
            format="json",
        )
        deleted = self.client.delete(
            reverse("talent-pool-member-detail", args=(pool.id, member_id))
        )

        self.assertEqual(added.status_code, status.HTTP_201_CREATED)
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        self.assertEqual(updated.data["private_notes"], "Call next week")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TalentPoolMember.objects.filter(pk=member_id).exists())

    def test_duplicate_pool_members_and_inaccessible_students_are_rejected(self):
        pool = TalentPool.objects.create(
            company=self.company,
            created_by=self.recruiter,
            name="Frontend",
        )
        url = reverse("talent-pool-member-create", args=(pool.id,))
        first = self.client.post(url, {"student_id": self.visible_student.id}, format="json")
        duplicate = self.client.post(url, {"student_id": self.visible_student.id}, format="json")
        hidden = self.client.post(url, {"student_id": self.hidden_student.id}, format="json")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(hidden.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_company_cannot_access_pool(self):
        pool = TalentPool.objects.create(
            company=self.company,
            created_by=self.recruiter,
            name="Private pool",
        )
        other_company = Company.objects.create(
            name="Other Talent Company",
            industry="Services",
            website="https://other-talent.example.com",
            contact_email="hr@other-talent.example.com",
        )
        outsider = self.create_recruiter("outsider@talent.example.com", other_company)
        self.client.force_authenticate(outsider)

        response = self.client.get(reverse("talent-pool-detail", args=(pool.id,)))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_pool_stops_exposing_candidate_when_student_becomes_hidden(self):
        pool = TalentPool.objects.create(
            company=self.company,
            created_by=self.recruiter,
            name="Privacy test",
        )
        TalentPoolMember.objects.create(
            pool=pool,
            student=self.visible_student,
            added_by=self.recruiter,
        )
        self.visible_student.is_visible_to_recruiters = False
        self.visible_student.save(update_fields=("is_visible_to_recruiters", "updated_at"))

        response = self.client.get(reverse("talent-pool-detail", args=(pool.id,)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["member_count"], 0)
        self.assertEqual(response.data["members"], [])

    def test_students_cannot_access_recruiter_talent_endpoints(self):
        self.client.force_authenticate(self.visible_student.user)

        response = self.client.get(reverse("talent-candidate-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
