from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from colleges.models import AcademicProgram, College, CollegeAdminProfile
from companies.models import Company, CompanyCollegePartnership, RecruiterProfile
from students.models import Skill, StudentProfile, StudentSkill

from .models import Opportunity, OpportunityBookmark, OpportunityCollegeInvitation


class OpportunityTests(APITestCase):
    def setUp(self):
        self.college_a = College.objects.create(name="Opportunity College A", code="OCA")
        self.college_b = College.objects.create(name="Opportunity College B", code="OCB")
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
            name="Hiring Technologies",
            industry="Technology",
            website="https://hiring.example.com",
            contact_email="hr@hiring.example.com",
        )
        self.recruiter = User.objects.create_user(
            email="jobs@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.RECRUITER,
        )
        RecruiterProfile.objects.create(
            user=self.recruiter,
            company=self.company,
            designation="Recruiter",
            is_company_owner=True,
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
        self.college_admin = User.objects.create_user(
            email="placement@opportunity-college.example.com",
            password="A-strong-test-password-2048",
            role=User.Role.ADMIN,
            is_staff=True,
        )
        CollegeAdminProfile.objects.create(
            user=self.college_admin,
            college=self.college_a,
            employee_id="OPP-ADMIN",
        )
        self.student_a = self.create_student(
            "eligible@example.com", self.college_a, self.program_a, "OCA001", Decimal("8.50"), 0
        )
        self.student_b = self.create_student(
            "other-college@example.com", self.college_b, self.program_b, "OCB001", Decimal("9.00"), 0
        )
        django_skill = Skill.objects.create(name="Django")
        StudentSkill.objects.create(
            student=self.student_a.student_profile,
            skill=django_skill,
            proficiency=StudentSkill.Proficiency.ADVANCED,
        )
        self.payload = {
            "title": "Backend Developer",
            "opportunity_type": "JOB",
            "description": "Build and maintain placement platform APIs.",
            "location": "Bengaluru",
            "work_mode": "HYBRID",
            "openings": 3,
            "compensation_min": "600000.00",
            "compensation_max": "900000.00",
            "compensation_period": "YEAR",
            "application_deadline": str(timezone.localdate() + timedelta(days=20)),
            "min_cgpa": "7.00",
            "max_active_backlogs": 0,
            "graduation_year_from": 2027,
            "graduation_year_to": 2028,
            "target_college_ids": [],
            "eligible_program_ids": [],
            "required_skill_names": ["Django", "REST APIs"],
            "status": "DRAFT",
        }

    @staticmethod
    def create_student(email, college, program, enrollment, cgpa, backlogs):
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
            cgpa=cgpa,
            active_backlogs=backlogs,
        )
        return user

    def create_opportunity(self, payload=None):
        self.client.force_authenticate(self.recruiter)
        return self.client.post(
            reverse("recruiter-opportunity-list"),
            payload or self.payload,
            format="json",
        )

    def create_approved_opportunity(self):
        draft = self.create_opportunity()
        sent = self.client.post(
            reverse("recruiter-opportunity-college-share", args=(draft.data["id"],)),
            {
                "college_ids": [self.college_a.id],
                "eligible_program_ids": [self.program_a.id],
                "recruiter_message": "Please review this campus opportunity.",
            },
            format="json",
        )
        invitation_id = sent.data["college_invitations"][0]["id"]
        self.client.force_authenticate(self.college_admin)
        self.client.patch(
            reverse("admin-opportunity-invitation-review", args=(invitation_id,)),
            {"status": "APPROVED", "review_note": "Approved for students."},
            format="json",
        )
        self.client.force_authenticate(self.recruiter)
        return self.client.get(reverse("recruiter-opportunity-detail", args=(draft.data["id"],)))

    def test_college_approval_publishes_opportunity_to_verified_college(self):
        response = self.create_approved_opportunity()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["company"]["name"], self.company.name)
        self.assertEqual(response.data["target_colleges"][0]["id"], self.college_a.id)
        self.assertIsNotNone(response.data["published_at"])
        self.assertEqual(response.data["required_skills"], ["Django", "REST APIs"])

    def test_recruiter_cannot_target_unverified_college(self):
        draft = self.create_opportunity()
        response = self.client.post(
            reverse("recruiter-opportunity-college-share", args=(draft.data["id"],)),
            {"college_ids": [self.college_b.id], "eligible_program_ids": [self.program_b.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("college_ids", response.data)

    def test_recruiter_cannot_publish_without_an_approved_target_college(self):
        payload = {**self.payload, "status": "PUBLISHED"}

        create_response = self.create_opportunity(payload)

        self.assertEqual(create_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", create_response.data)

    def test_recruiter_can_save_a_draft_before_selecting_colleges(self):
        payload = {
            **self.payload,
            "status": "DRAFT",
            "target_college_ids": [],
            "eligible_program_ids": [],
        }

        create_response = self.create_opportunity(payload)

        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["status"], Opportunity.Status.DRAFT)
        self.assertEqual(create_response.data["target_colleges"], [])

    def test_recruiter_creates_first_then_sends_opportunity_to_colleges(self):
        draft = self.create_opportunity()

        share_response = self.client.post(
            reverse("recruiter-opportunity-college-share", args=(draft.data["id"],)),
            {
                "college_ids": [self.college_a.id],
                "eligible_program_ids": [self.program_a.id],
            },
            format="json",
        )

        self.assertEqual(draft.status_code, status.HTTP_201_CREATED)
        self.assertEqual(draft.data["target_colleges"], [])
        self.assertEqual(share_response.status_code, status.HTTP_200_OK)
        self.assertEqual(share_response.data["status"], Opportunity.Status.DRAFT)
        self.assertEqual(share_response.data["target_colleges"], [])
        self.assertEqual(share_response.data["college_invitations"][0]["status"], "PENDING")

    def test_program_must_belong_to_target_college(self):
        draft = self.create_opportunity()
        response = self.client.post(
            reverse("recruiter-opportunity-college-share", args=(draft.data["id"],)),
            {"college_ids": [self.college_a.id], "eligible_program_ids": [self.program_b.id]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("eligible_program_ids", response.data)

    def test_college_admin_sees_and_rejects_only_own_opportunity_invitations(self):
        draft = self.create_opportunity()
        sent = self.client.post(
            reverse("recruiter-opportunity-college-share", args=(draft.data["id"],)),
            {"college_ids": [self.college_a.id], "eligible_program_ids": [self.program_a.id]},
            format="json",
        )
        invitation_id = sent.data["college_invitations"][0]["id"]
        self.client.force_authenticate(self.college_admin)

        listing = self.client.get(reverse("admin-opportunity-invitation-list"), {"status": "PENDING"})
        rejected = self.client.patch(
            reverse("admin-opportunity-invitation-review", args=(invitation_id,)),
            {"status": "REJECTED", "review_note": "Deadline is too soon."},
            format="json",
        )

        self.assertEqual(listing.data["count"], 1)
        self.assertEqual(rejected.status_code, status.HTTP_200_OK)
        self.assertEqual(rejected.data["status"], "REJECTED")
        self.assertEqual(rejected.data["review_note"], "Deadline is too soon.")
        self.assertFalse(Opportunity.objects.get(pk=draft.data["id"]).target_colleges.exists())

    def test_rejection_requires_a_reason(self):
        draft = self.create_opportunity()
        sent = self.client.post(
            reverse("recruiter-opportunity-college-share", args=(draft.data["id"],)),
            {"college_ids": [self.college_a.id]},
            format="json",
        )
        invitation_id = sent.data["college_invitations"][0]["id"]
        self.client.force_authenticate(self.college_admin)

        response = self.client.patch(
            reverse("admin-opportunity-invitation-review", args=(invitation_id,)),
            {"status": "REJECTED", "review_note": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("review_note", response.data)

    def test_recruiter_can_retry_rejected_invitation_and_withdraw_pending_request(self):
        draft = self.create_opportunity()
        share_url = reverse("recruiter-opportunity-college-share", args=(draft.data["id"],))
        sent = self.client.post(share_url, {"college_ids": [self.college_a.id]}, format="json")
        invitation_id = sent.data["college_invitations"][0]["id"]
        invitation = OpportunityCollegeInvitation.objects.get(pk=invitation_id)
        invitation.status = OpportunityCollegeInvitation.Status.REJECTED
        invitation.review_note = "Update the details."
        invitation.save(update_fields=("status", "review_note", "updated_at"))

        retried = self.client.post(
            share_url,
            {"college_ids": [self.college_a.id], "recruiter_message": "Details updated."},
            format="json",
        )
        withdrawn = self.client.delete(
            reverse("recruiter-opportunity-invitation-detail", args=(invitation_id,))
        )
        invitation.refresh_from_db()

        self.assertEqual(retried.status_code, status.HTTP_200_OK)
        self.assertEqual(retried.data["college_invitations"][0]["status"], "PENDING")
        self.assertEqual(withdrawn.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(invitation.status, OpportunityCollegeInvitation.Status.WITHDRAWN)

    def test_material_edit_requires_college_reapproval(self):
        approved = self.create_approved_opportunity().data

        response = self.client.patch(
            reverse("recruiter-opportunity-detail", args=(approved["id"],)),
            {"min_cgpa": "8.00"},
            format="json",
        )

        invitation = OpportunityCollegeInvitation.objects.get(opportunity_id=approved["id"])
        opportunity = Opportunity.objects.get(pk=approved["id"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(invitation.status, OpportunityCollegeInvitation.Status.PENDING)
        self.assertFalse(opportunity.target_colleges.exists())

    def test_student_sees_only_published_current_opportunities_for_own_college(self):
        published = self.create_approved_opportunity().data
        self.client.force_authenticate(self.student_a)

        own_response = self.client.get(reverse("student-opportunity-list"))
        self.client.force_authenticate(self.student_b)
        other_response = self.client.get(reverse("student-opportunity-list"))

        self.assertEqual(own_response.status_code, status.HTTP_200_OK)
        self.assertEqual(own_response.data["count"], 1)
        self.assertEqual(own_response.data["results"][0]["id"], published["id"])
        self.assertTrue(own_response.data["results"][0]["is_eligible"])
        self.assertEqual(own_response.data["results"][0]["matched_skills"], ["Django"])
        self.assertEqual(other_response.data["count"], 0)

    def test_student_receives_clear_ineligibility_reasons(self):
        response = self.create_approved_opportunity().data
        self.student_a.student_profile.cgpa = Decimal("6.50")
        self.student_a.student_profile.active_backlogs = 2
        self.student_a.student_profile.save(update_fields=("cgpa", "active_backlogs", "updated_at"))
        self.client.force_authenticate(self.student_a)

        detail = self.client.get(reverse("student-opportunity-detail", args=(response["id"],)))

        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertFalse(detail.data["is_eligible"])
        self.assertEqual(len(detail.data["eligibility_reasons"]), 2)

    def test_other_company_recruiter_cannot_manage_opportunity(self):
        opportunity_id = self.create_opportunity().data["id"]
        other_company = Company.objects.create(
            name="Other Employer",
            industry="Finance",
            website="https://other.example.com",
            contact_email="hr@other.example.com",
        )
        other_recruiter = User.objects.create_user(
            email="other-recruiter@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.RECRUITER,
        )
        RecruiterProfile.objects.create(
            user=other_recruiter,
            company=other_company,
            designation="Recruiter",
        )
        self.client.force_authenticate(other_recruiter)

        response = self.client.get(reverse("recruiter-opportunity-detail", args=(opportunity_id,)))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_published_opportunity_must_be_closed_not_deleted(self):
        opportunity_id = self.create_approved_opportunity().data["id"]

        delete_response = self.client.delete(reverse("recruiter-opportunity-detail", args=(opportunity_id,)))
        close_response = self.client.patch(
            reverse("recruiter-opportunity-detail", args=(opportunity_id,)),
            {"status": Opportunity.Status.CLOSED},
            format="json",
        )

        self.assertEqual(delete_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(close_response.status_code, status.HTTP_200_OK)
        self.assertEqual(close_response.data["status"], Opportunity.Status.CLOSED)

    def test_student_receives_explainable_ranked_recommendations(self):
        opportunity_id = self.create_approved_opportunity().data["id"]
        self.student_a.student_profile.preferred_job_role = "Backend Developer"
        self.student_a.student_profile.preferred_locations = "Bengaluru, Pune"
        self.student_a.student_profile.save(update_fields=("preferred_job_role", "preferred_locations", "updated_at"))
        self.client.force_authenticate(self.student_a)

        response = self.client.get(reverse("student-opportunity-recommended"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["id"], opportunity_id)
        self.assertGreater(response.data[0]["match_score"], 50)
        self.assertTrue(response.data[0]["match_reasons"])

    def test_student_can_save_filter_and_remove_an_opportunity(self):
        opportunity_id = self.create_approved_opportunity().data["id"]
        self.client.force_authenticate(self.student_a)

        saved = self.client.post(reverse("student-opportunity-save", args=(opportunity_id,)))
        filtered = self.client.get(reverse("student-opportunity-list"), {"saved_only": "true"})
        removed = self.client.delete(reverse("student-opportunity-save", args=(opportunity_id,)))

        self.assertEqual(saved.data["is_saved"], True)
        self.assertEqual(filtered.data["count"], 1)
        self.assertEqual(filtered.data["results"][0]["is_saved"], True)
        self.assertEqual(removed.data["is_saved"], False)
        self.assertFalse(OpportunityBookmark.objects.filter(student=self.student_a.student_profile).exists())

    def test_advanced_filters_limit_student_results(self):
        self.create_approved_opportunity()
        self.client.force_authenticate(self.student_a)

        matching = self.client.get(reverse("student-opportunity-list"), {
            "company": "Hiring Tech",
            "skill": "Django",
            "min_compensation": "800000",
            "eligible_only": "true",
        })
        missing = self.client.get(reverse("student-opportunity-list"), {"company": "Unknown Employer"})

        self.assertEqual(matching.data["count"], 1)
        self.assertEqual(missing.data["count"], 0)

    def test_student_cannot_save_an_opportunity_hidden_from_their_college(self):
        opportunity_id = self.create_opportunity().data["id"]
        self.client.force_authenticate(self.student_b)

        response = self.client.post(reverse("student-opportunity-save", args=(opportunity_id,)))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
