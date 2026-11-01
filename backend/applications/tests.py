from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from colleges.models import AcademicProgram, College
from companies.models import Company, CompanyCollegePartnership, RecruiterProfile
from opportunities.models import Opportunity
from placements.models import CollegePlacementPolicy
from students.models import StudentProfile, StudentResume

from .models import Application, InterviewSchedule, RecruitmentRound


class ApplicationTests(APITestCase):
    def setUp(self):
        self.college = College.objects.create(name="Application College", code="APC")
        self.other_college = College.objects.create(name="Other College", code="OTC")
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
        self.company = Company.objects.create(
            name="Application Systems",
            industry="Technology",
            website="https://application.example.com",
            contact_email="hr@application.example.com",
        )
        self.recruiter = self.create_recruiter("recruiter@app.example.com", self.company)
        CompanyCollegePartnership.objects.create(
            company=self.company,
            college=self.college,
            status=CompanyCollegePartnership.Status.VERIFIED,
        )
        self.student = self.create_student(
            "student@app.example.com", self.college, self.program, "APC001", Decimal("8.50")
        )
        self.resume = self.create_resume(self.student.student_profile, "Primary resume")
        self.opportunity = Opportunity.objects.create(
            company=self.company,
            created_by=self.recruiter,
            title="Django Developer",
            opportunity_type=Opportunity.Type.JOB,
            description="Build APIs.",
            location="Bengaluru",
            work_mode=Opportunity.WorkMode.HYBRID,
            application_deadline=timezone.localdate() + timedelta(days=10),
            min_cgpa=Decimal("7.00"),
            max_active_backlogs=0,
            status=Opportunity.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        self.opportunity.target_colleges.add(self.college)
        self.opportunity.eligible_programs.add(self.program)

    @staticmethod
    def create_recruiter(email, company):
        user = User.objects.create_user(
            email=email,
            password="A-strong-test-password-2048",
            role=User.Role.RECRUITER,
        )
        RecruiterProfile.objects.create(user=user, company=company, designation="Recruiter")
        return user

    @staticmethod
    def create_student(email, college, program, enrollment, cgpa):
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
        )
        return user

    @staticmethod
    def create_resume(student, title):
        return StudentResume.objects.bulk_create([
            StudentResume(
                student=student,
                title=title,
                file="students/resumes/test.pdf",
                original_filename="test.pdf",
                file_size=100,
                is_primary=True,
            )
        ])[0]

    def apply(self, student=None, opportunity=None, resume=None):
        self.client.force_authenticate(student or self.student)
        return self.client.post(
            reverse("student-application-list"),
            {
                "opportunity_id": (opportunity or self.opportunity).id,
                "resume_id": (resume or self.resume).id,
                "cover_letter": "I would like to apply for this role.",
            },
            format="json",
        )

    def test_eligible_student_can_apply_with_status_history(self):
        response = self.apply()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Application.Status.APPLIED)
        self.assertEqual(response.data["resume"]["id"], self.resume.id)
        self.assertEqual(len(response.data["status_history"]), 1)
        self.assertEqual(response.data["status_history"][0]["to_status"], Application.Status.APPLIED)

    def test_student_cannot_apply_twice(self):
        self.apply()

        response = self.apply()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("opportunity_id", response.data)

    def test_ineligible_student_cannot_apply(self):
        self.student.student_profile.cgpa = Decimal("6.00")
        self.student.student_profile.save(update_fields=("cgpa", "updated_at"))

        response = self.apply()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Minimum CGPA required", str(response.data["opportunity_id"]))

    def test_college_policy_can_pause_student_applications(self):
        CollegePlacementPolicy.objects.create(
            college=self.college,
            applications_enabled=False,
            student_message="Applications are paused while records are reviewed.",
        )

        response = self.apply()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Applications are paused", str(response.data["opportunity_id"]))

    def test_college_policy_requirements_are_enforced_with_opportunity_rules(self):
        CollegePlacementPolicy.objects.create(
            college=self.college,
            require_verified_documents=True,
            minimum_cgpa=Decimal("9.00"),
        )

        response = self.apply()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        reasons = str(response.data["opportunity_id"])
        self.assertIn("required academic documents", reasons)
        self.assertIn("minimum CGPA of 9.00", reasons)

    def test_student_cannot_apply_with_another_students_resume(self):
        other_student = self.create_student(
            "resume-owner@app.example.com", self.college, self.program, "APC002", Decimal("8.00")
        )
        other_resume = self.create_resume(other_student.student_profile, "Other resume")

        response = self.apply(resume=other_resume)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("resume_id", response.data)

    def test_student_cannot_apply_to_another_colleges_opportunity(self):
        self.opportunity.target_colleges.set([self.other_college])

        response = self.apply()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("opportunity_id", response.data)

    def test_student_can_withdraw_active_application(self):
        application_id = self.apply().data["id"]

        response = self.client.post(reverse("student-application-withdraw", args=(application_id,)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Application.Status.WITHDRAWN)
        self.assertEqual(len(response.data["status_history"]), 2)

    def test_recruiter_can_review_own_company_application(self):
        application_id = self.apply().data["id"]
        self.client.force_authenticate(self.recruiter)

        response = self.client.patch(
            reverse("recruiter-application-detail", args=(application_id,)),
            {"status": Application.Status.SHORTLISTED, "note": "Strong Django profile."},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], Application.Status.SHORTLISTED)
        self.assertEqual(response.data["status_history"][-1]["note"], "Strong Django profile.")

    def test_recruiter_cannot_reverse_or_change_terminal_status(self):
        application_id = self.apply().data["id"]
        self.client.force_authenticate(self.recruiter)
        self.client.patch(
            reverse("recruiter-application-detail", args=(application_id,)),
            {"status": Application.Status.REJECTED},
            format="json",
        )

        response = self.client.patch(
            reverse("recruiter-application-detail", args=(application_id,)),
            {"status": Application.Status.SHORTLISTED},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_other_company_recruiter_cannot_view_application(self):
        application_id = self.apply().data["id"]
        other_company = Company.objects.create(
            name="Unrelated Company",
            industry="Finance",
            website="https://unrelated.example.com",
            contact_email="hr@unrelated.example.com",
        )
        other_recruiter = self.create_recruiter("other@app.example.com", other_company)
        self.client.force_authenticate(other_recruiter)

        response = self.client.get(reverse("recruiter-application-detail", args=(application_id,)))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def create_round(self):
        self.client.force_authenticate(self.recruiter)
        return self.client.post(
            reverse("recruiter-round-list"),
            {
                "opportunity_id": self.opportunity.id,
                "name": "Technical Round",
                "round_type": RecruitmentRound.Type.TECHNICAL,
                "sequence": 1,
                "description": "Django and problem-solving interview.",
            },
            format="json",
        )

    def shortlist_application(self):
        application_id = self.apply().data["id"]
        self.client.force_authenticate(self.recruiter)
        self.client.patch(
            reverse("recruiter-application-detail", args=(application_id,)),
            {"status": Application.Status.SHORTLISTED},
            format="json",
        )
        return application_id

    def schedule_interview(self, application_id, round_id, **overrides):
        payload = {
            "recruitment_round_id": round_id,
            "application_id": application_id,
            "scheduled_at": (timezone.now() + timedelta(days=2)).isoformat(),
            "duration_minutes": 60,
            "mode": InterviewSchedule.Mode.ONLINE,
            "meeting_link": "https://meet.example.com/technical",
            "instructions": "Join five minutes early.",
        }
        payload.update(overrides)
        self.client.force_authenticate(self.recruiter)
        return self.client.post(reverse("recruiter-interview-list"), payload, format="json")

    def test_recruiter_can_create_ordered_round_for_own_opportunity(self):
        response = self.create_round()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["sequence"], 1)
        self.assertEqual(response.data["round_type_display"], "Technical interview")

    def test_round_sequence_must_be_unique_per_opportunity(self):
        self.create_round()

        response = self.create_round()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sequence", response.data)

    def test_scheduling_shortlisted_candidate_moves_application_to_interview(self):
        application_id = self.shortlist_application()
        round_id = self.create_round().data["id"]

        response = self.schedule_interview(application_id, round_id)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], InterviewSchedule.Status.SCHEDULED)
        application = Application.objects.get(pk=application_id)
        self.assertEqual(application.status, Application.Status.INTERVIEW)
        self.assertEqual(application.status_history.last().to_status, Application.Status.INTERVIEW)

    def test_candidate_must_be_shortlisted_before_scheduling(self):
        application_id = self.apply().data["id"]
        round_id = self.create_round().data["id"]

        response = self.schedule_interview(application_id, round_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("application_id", response.data)

    def test_online_interview_requires_meeting_link(self):
        application_id = self.shortlist_application()
        round_id = self.create_round().data["id"]

        response = self.schedule_interview(application_id, round_id, meeting_link="")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("meeting_link", response.data)

    def test_recruiter_can_complete_interview_with_result_and_feedback(self):
        application_id = self.shortlist_application()
        round_id = self.create_round().data["id"]
        interview_id = self.schedule_interview(application_id, round_id).data["id"]

        response = self.client.patch(
            reverse("recruiter-interview-detail", args=(interview_id,)),
            {
                "status": InterviewSchedule.Status.COMPLETED,
                "result": InterviewSchedule.Result.PASSED,
                "feedback": "Strong technical fundamentals.",
                "rating": 5,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["result"], InterviewSchedule.Result.PASSED)
        self.assertEqual(response.data["rating"], 5)

    def test_student_sees_own_schedule_without_private_feedback(self):
        application_id = self.shortlist_application()
        round_id = self.create_round().data["id"]
        interview_id = self.schedule_interview(application_id, round_id).data["id"]
        self.client.patch(
            reverse("recruiter-interview-detail", args=(interview_id,)),
            {
                "status": InterviewSchedule.Status.COMPLETED,
                "result": InterviewSchedule.Result.PASSED,
                "feedback": "Private recruiter feedback.",
            },
            format="json",
        )
        self.client.force_authenticate(self.student)

        response = self.client.get(reverse("student-interview-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertNotIn("feedback", response.data["results"][0])
