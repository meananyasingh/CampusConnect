from django.db import IntegrityError, transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accounts.serializers import UserSerializer
from companies.models import CompanyCollegePartnership
from companies.serializers import CompanySummarySerializer
from opportunities.models import Opportunity
from opportunities.services import get_eligibility_reasons
from notifications.models import Notification
from notifications.services import create_notification, notify_company_recruiters
from students.models import StudentProfile, StudentResume

from .models import (
    Application,
    ApplicationStatusHistory,
    InterviewSchedule,
    RecruitmentRound,
)


class ApplicationOpportunitySerializer(serializers.ModelSerializer):
    company = CompanySummarySerializer(read_only=True)
    opportunity_type_display = serializers.CharField(source="get_opportunity_type_display", read_only=True)
    work_mode_display = serializers.CharField(source="get_work_mode_display", read_only=True)

    class Meta:
        model = Opportunity
        fields = (
            "id", "company", "title", "opportunity_type", "opportunity_type_display",
            "location", "work_mode", "work_mode_display", "application_deadline",
        )


class ApplicationResumeSerializer(serializers.ModelSerializer):
    file_url = serializers.FileField(source="file", read_only=True)

    class Meta:
        model = StudentResume
        fields = ("id", "title", "original_filename", "file_url")


class ApplicantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    college_name = serializers.CharField(source="college.name", read_only=True)
    program_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = (
            "id", "user", "college_name", "program_name", "enrollment_number",
            "graduation_year", "cgpa", "active_backlogs", "phone",
        )

    @extend_schema_field(serializers.CharField())
    def get_program_name(self, student):
        return f"{student.program.get_degree_display()} — {student.program.branch}"


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    from_status_display = serializers.SerializerMethodField()
    to_status_display = serializers.CharField(source="get_to_status_display", read_only=True)
    changed_by_name = serializers.SerializerMethodField()
    changed_by_role = serializers.CharField(source="changed_by.role", read_only=True)

    class Meta:
        model = ApplicationStatusHistory
        fields = (
            "id", "from_status", "from_status_display", "to_status",
            "to_status_display", "changed_by_name", "changed_by_role", "note", "created_at",
        )

    @extend_schema_field(serializers.CharField())
    def get_from_status_display(self, history):
        return history.get_from_status_display() if history.from_status else "Application created"

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_changed_by_name(self, history):
        if history.changed_by is None:
            return None
        return history.changed_by.get_full_name() or history.changed_by.get_role_display()


class ApplicationSerializer(serializers.ModelSerializer):
    opportunity = ApplicationOpportunitySerializer(read_only=True)
    opportunity_id = serializers.PrimaryKeyRelatedField(
        source="opportunity",
        queryset=Opportunity.objects.all(),
        write_only=True,
    )
    student = ApplicantSerializer(read_only=True)
    resume = ApplicationResumeSerializer(read_only=True)
    resume_id = serializers.PrimaryKeyRelatedField(
        source="resume",
        queryset=StudentResume.objects.all(),
        write_only=True,
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    status_history = ApplicationStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = (
            "id", "opportunity", "opportunity_id", "student", "resume", "resume_id",
            "cover_letter", "status", "status_display", "status_history", "applied_at", "updated_at",
        )
        read_only_fields = (
            "id", "student", "status", "status_display", "status_history", "applied_at", "updated_at",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        student = self.context["request"].user.student_profile
        opportunity = attrs["opportunity"]
        resume = attrs["resume"]

        if resume.student_id != student.id:
            raise serializers.ValidationError({"resume_id": "Select one of your own resumes."})
        if Application.objects.filter(opportunity=opportunity, student=student).exists():
            raise serializers.ValidationError({"opportunity_id": "You have already applied for this opportunity."})
        if opportunity.status != Opportunity.Status.PUBLISHED:
            raise serializers.ValidationError({"opportunity_id": "This opportunity is not accepting applications."})
        if opportunity.application_deadline < timezone.localdate():
            raise serializers.ValidationError({"opportunity_id": "The application deadline has passed."})
        if not opportunity.target_colleges.filter(pk=student.college_id).exists():
            raise serializers.ValidationError({"opportunity_id": "This opportunity was not shared with your college."})
        if not CompanyCollegePartnership.objects.filter(
            company=opportunity.company,
            college=student.college,
            status=CompanyCollegePartnership.Status.VERIFIED,
        ).exists():
            raise serializers.ValidationError({"opportunity_id": "This company is not approved by your college."})
        reasons = get_eligibility_reasons(opportunity, student)
        from placements.services import get_college_policy_blockers

        reasons.extend(get_college_policy_blockers(student))
        if reasons:
            raise serializers.ValidationError({"opportunity_id": reasons})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        try:
            application = Application.objects.create(
                student=self.context["request"].user.student_profile,
                **validated_data,
            )
        except IntegrityError as error:
            raise serializers.ValidationError(
                {"opportunity_id": "You have already applied for this opportunity."}
            ) from error
        ApplicationStatusHistory.objects.create(
            application=application,
            to_status=Application.Status.APPLIED,
            changed_by=self.context["request"].user,
            note="Application submitted by student.",
        )
        notify_company_recruiters(
            company=application.opportunity.company,
            category=Notification.Category.APPLICATION,
            title="New candidate application",
            message=f"A student applied for {application.opportunity.title}.",
            link=f"/recruiter/applications?opportunity={application.opportunity_id}",
        )
        return application


class RecruiterApplicationStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=(
        Application.Status.UNDER_REVIEW,
        Application.Status.SHORTLISTED,
        Application.Status.SELECTED,
        Application.Status.REJECTED,
    ))
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate_status(self, target_status):
        current_status = self.context["application"].status
        transitions = {
            Application.Status.APPLIED: {
                Application.Status.UNDER_REVIEW,
                Application.Status.SHORTLISTED,
                Application.Status.REJECTED,
            },
            Application.Status.UNDER_REVIEW: {
                Application.Status.SHORTLISTED,
                Application.Status.REJECTED,
            },
            Application.Status.SHORTLISTED: {
                Application.Status.SELECTED,
                Application.Status.REJECTED,
            },
            Application.Status.INTERVIEW: {
                Application.Status.SELECTED,
                Application.Status.REJECTED,
            },
            Application.Status.SELECTED: set(),
            Application.Status.REJECTED: set(),
            Application.Status.WITHDRAWN: set(),
        }
        if target_status not in transitions[current_status]:
            raise serializers.ValidationError("This application status change is not allowed.")
        return target_status

    @transaction.atomic
    def save(self, **kwargs):
        application = self.context["application"]
        previous_status = application.status
        application.status = self.validated_data["status"]
        application.save(update_fields=("status", "updated_at"))
        ApplicationStatusHistory.objects.create(
            application=application,
            from_status=previous_status,
            to_status=application.status,
            changed_by=self.context["request"].user,
            note=self.validated_data.get("note", ""),
        )
        create_notification(
            recipient=application.student.user,
            category=Notification.Category.APPLICATION,
            title=f"Application {application.get_status_display().lower()}",
            message=f"Your application for {application.opportunity.title} is now {application.get_status_display().lower()}.",
            link="/student/applications",
        )
        application._prefetched_objects_cache = {}
        return application


class RecruitmentRoundSerializer(serializers.ModelSerializer):
    opportunity = ApplicationOpportunitySerializer(read_only=True)
    opportunity_id = serializers.PrimaryKeyRelatedField(
        source="opportunity",
        queryset=Opportunity.objects.all(),
        write_only=True,
    )
    round_type_display = serializers.CharField(source="get_round_type_display", read_only=True)
    interview_count = serializers.SerializerMethodField()

    class Meta:
        model = RecruitmentRound
        fields = (
            "id", "opportunity", "opportunity_id", "name", "round_type",
            "round_type_display", "sequence", "description", "interview_count",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "interview_count", "created_at", "updated_at")
        validators = []

    @extend_schema_field(serializers.IntegerField())
    def get_interview_count(self, recruitment_round):
        annotated_count = getattr(recruitment_round, "interview_count", None)
        return annotated_count if annotated_count is not None else recruitment_round.interviews.count()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        opportunity = attrs.get("opportunity", getattr(self.instance, "opportunity", None))
        company = self.context["request"].user.recruiter_profile.company
        if opportunity.company_id != company.id:
            raise serializers.ValidationError({"opportunity_id": "Select one of your company's opportunities."})
        if opportunity.status in {Opportunity.Status.DRAFT, Opportunity.Status.CANCELLED}:
            raise serializers.ValidationError(
                {"opportunity_id": "Rounds can only be configured after an opportunity is sent to colleges."}
            )
        if self.instance and "opportunity" in attrs and opportunity.id != self.instance.opportunity_id:
            raise serializers.ValidationError({"opportunity_id": "A round cannot be moved to another opportunity."})
        sequence = attrs.get("sequence", getattr(self.instance, "sequence", None))
        duplicate = RecruitmentRound.objects.filter(opportunity=opportunity, sequence=sequence)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError({"sequence": "This opportunity already has a round at that position."})
        return attrs


class InterviewScheduleSerializer(serializers.ModelSerializer):
    recruitment_round = RecruitmentRoundSerializer(read_only=True)
    recruitment_round_id = serializers.PrimaryKeyRelatedField(
        source="recruitment_round",
        queryset=RecruitmentRound.objects.all(),
        write_only=True,
    )
    application = ApplicationSerializer(read_only=True)
    application_id = serializers.PrimaryKeyRelatedField(
        source="application",
        queryset=Application.objects.all(),
        write_only=True,
    )
    mode_display = serializers.CharField(source="get_mode_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    result_display = serializers.CharField(source="get_result_display", read_only=True)

    class Meta:
        model = InterviewSchedule
        fields = (
            "id", "recruitment_round", "recruitment_round_id", "application",
            "application_id", "scheduled_at", "duration_minutes", "mode", "mode_display",
            "venue", "meeting_link", "instructions", "status", "status_display",
            "result", "result_display", "feedback", "rating", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        validators = []

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance
        recruitment_round = attrs.get("recruitment_round", getattr(instance, "recruitment_round", None))
        application = attrs.get("application", getattr(instance, "application", None))
        company = self.context["request"].user.recruiter_profile.company

        if recruitment_round.opportunity.company_id != company.id or application.opportunity.company_id != company.id:
            raise serializers.ValidationError("You can only schedule interviews for your own company.")
        if instance and (
            ("recruitment_round" in attrs and recruitment_round.id != instance.recruitment_round_id)
            or ("application" in attrs and application.id != instance.application_id)
        ):
            raise serializers.ValidationError("An interview cannot be moved to another round or application.")
        if recruitment_round.opportunity_id != application.opportunity_id:
            raise serializers.ValidationError(
                {"application_id": "The candidate did not apply for this round's opportunity."}
            )
        if not instance and application.status not in {
            Application.Status.SHORTLISTED,
            Application.Status.INTERVIEW,
        }:
            raise serializers.ValidationError(
                {"application_id": "Shortlist the candidate before scheduling an interview."}
            )
        if not instance and InterviewSchedule.objects.filter(
            recruitment_round=recruitment_round,
            application=application,
        ).exists():
            raise serializers.ValidationError(
                {"application_id": "This candidate is already scheduled for the selected round."}
            )

        scheduled_at = attrs.get("scheduled_at", getattr(instance, "scheduled_at", None))
        interview_status = attrs.get("status", getattr(instance, "status", InterviewSchedule.Status.SCHEDULED))
        result = attrs.get("result", getattr(instance, "result", InterviewSchedule.Result.PENDING))
        mode = attrs.get("mode", getattr(instance, "mode", None))
        venue = attrs.get("venue", getattr(instance, "venue", ""))
        meeting_link = attrs.get("meeting_link", getattr(instance, "meeting_link", ""))

        if interview_status == InterviewSchedule.Status.SCHEDULED and scheduled_at <= timezone.now():
            raise serializers.ValidationError({"scheduled_at": "A scheduled interview must be in the future."})
        if mode == InterviewSchedule.Mode.ONLINE and not meeting_link:
            raise serializers.ValidationError({"meeting_link": "Add a meeting link for an online interview."})
        if mode == InterviewSchedule.Mode.ONSITE and not venue:
            raise serializers.ValidationError({"venue": "Add a venue for an on-site interview."})
        if interview_status == InterviewSchedule.Status.COMPLETED and result == InterviewSchedule.Result.PENDING:
            raise serializers.ValidationError({"result": "Record the interview result when completing it."})
        if interview_status == InterviewSchedule.Status.SCHEDULED and result != InterviewSchedule.Result.PENDING:
            raise serializers.ValidationError({"result": "Complete the interview before recording its result."})
        if instance and "status" in attrs and attrs["status"] != instance.status:
            transitions = {
                InterviewSchedule.Status.SCHEDULED: {
                    InterviewSchedule.Status.COMPLETED,
                    InterviewSchedule.Status.CANCELLED,
                },
                InterviewSchedule.Status.COMPLETED: set(),
                InterviewSchedule.Status.CANCELLED: set(),
            }
            if attrs["status"] not in transitions[instance.status]:
                raise serializers.ValidationError({"status": "This interview status change is not allowed."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        application = validated_data["application"]
        interview = InterviewSchedule.objects.create(
            created_by=self.context["request"].user,
            **validated_data,
        )
        if application.status == Application.Status.SHORTLISTED:
            application.status = Application.Status.INTERVIEW
            application.save(update_fields=("status", "updated_at"))
            ApplicationStatusHistory.objects.create(
                application=application,
                from_status=Application.Status.SHORTLISTED,
                to_status=Application.Status.INTERVIEW,
                changed_by=self.context["request"].user,
                note=f"Scheduled for {interview.recruitment_round.name}.",
            )
        create_notification(
            recipient=application.student.user,
            category=Notification.Category.INTERVIEW,
            title="Interview scheduled",
            message=f"{interview.recruitment_round.name} for {application.opportunity.title} has been scheduled.",
            link="/student/interviews",
        )
        return interview

    def update(self, instance, validated_data):
        previous_status = instance.status
        previous_time = instance.scheduled_at
        interview = super().update(instance, validated_data)
        if interview.status != previous_status or interview.scheduled_at != previous_time:
            create_notification(
                recipient=interview.application.student.user,
                category=Notification.Category.INTERVIEW,
                title=f"Interview {interview.get_status_display().lower()}",
                message=f"{interview.recruitment_round.name} for {interview.application.opportunity.title} was updated.",
                link="/student/interviews",
            )
        return interview


class StudentInterviewScheduleSerializer(serializers.ModelSerializer):
    recruitment_round = RecruitmentRoundSerializer(read_only=True)
    opportunity = ApplicationOpportunitySerializer(source="application.opportunity", read_only=True)
    mode_display = serializers.CharField(source="get_mode_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    result_display = serializers.CharField(source="get_result_display", read_only=True)

    class Meta:
        model = InterviewSchedule
        fields = (
            "id", "recruitment_round", "opportunity", "scheduled_at", "duration_minutes",
            "mode", "mode_display", "venue", "meeting_link", "instructions",
            "status", "status_display", "result", "result_display", "created_at", "updated_at",
        )
