from datetime import date

from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from colleges.models import AcademicProgram, College
from colleges.serializers import AcademicProgramSerializer, CollegeSerializer
from companies.models import CompanyCollegePartnership
from companies.serializers import CompanySummarySerializer
from notifications.models import Notification
from notifications.services import notify_college_admins, notify_company_recruiters
from students.models import Skill

from .models import Opportunity, OpportunityCollegeInvitation
from .services import get_eligibility_reasons, sync_approved_opportunity_audience


class OpportunityInvitationSummarySerializer(serializers.ModelSerializer):
    college = CollegeSerializer(read_only=True)
    eligible_programs = AcademicProgramSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reviewed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = OpportunityCollegeInvitation
        fields = (
            "id", "college", "eligible_programs", "status", "status_display",
            "recruiter_message", "review_note", "reviewed_by_name", "submitted_at",
            "reviewed_at", "updated_at",
        )

    def get_reviewed_by_name(self, instance) -> str:
        if not instance.reviewed_by:
            return ""
        return instance.reviewed_by.get_full_name() or instance.reviewed_by.email


class OpportunitySerializer(serializers.ModelSerializer):
    company = CompanySummarySerializer(read_only=True)
    opportunity_type_display = serializers.CharField(source="get_opportunity_type_display", read_only=True)
    work_mode_display = serializers.CharField(source="get_work_mode_display", read_only=True)
    compensation_period_display = serializers.CharField(source="get_compensation_period_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    target_colleges = CollegeSerializer(many=True, read_only=True)
    target_college_ids = serializers.PrimaryKeyRelatedField(
        source="target_colleges",
        queryset=College.objects.filter(is_active=True),
        many=True,
        required=False,
        write_only=True,
    )
    eligible_programs = AcademicProgramSerializer(many=True, read_only=True)
    eligible_program_ids = serializers.PrimaryKeyRelatedField(
        source="eligible_programs",
        queryset=AcademicProgram.objects.filter(is_active=True, college__is_active=True),
        many=True,
        required=False,
        write_only=True,
    )
    required_skills = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")
    required_skill_names = serializers.ListField(
        child=serializers.CharField(max_length=80),
        required=False,
        write_only=True,
    )
    college_invitations = OpportunityInvitationSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Opportunity
        fields = (
            "id", "company", "title", "opportunity_type", "opportunity_type_display",
            "description", "responsibilities", "qualifications", "location", "work_mode",
            "work_mode_display", "openings", "compensation_min", "compensation_max",
            "compensation_period", "compensation_period_display", "application_deadline",
            "min_cgpa", "max_active_backlogs", "graduation_year_from", "graduation_year_to",
            "target_colleges", "target_college_ids", "eligible_programs", "eligible_program_ids",
            "required_skills", "required_skill_names", "status", "status_display", "published_at",
            "college_invitations", "created_at", "updated_at",
        )
        read_only_fields = ("id", "company", "published_at", "created_at", "updated_at")

    def validate_required_skill_names(self, values):
        normalized = []
        seen = set()
        for value in values:
            name = " ".join(value.split())
            if len(name) < 2:
                raise serializers.ValidationError("Each skill name must contain at least 2 characters.")
            key = name.casefold()
            if key not in seen:
                normalized.append(name)
                seen.add(key)
        return normalized

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs.get("target_colleges"):
            raise serializers.ValidationError(
                {"target_college_ids": "Create the opportunity first, then send it for college review."}
            )
        if attrs.get("eligible_programs"):
            raise serializers.ValidationError(
                {"eligible_program_ids": "Choose programs while sending the opportunity to colleges."}
            )
        if attrs.get("status") == Opportunity.Status.PUBLISHED and (
            self.instance is None or self.instance.status != Opportunity.Status.PUBLISHED
        ):
            raise serializers.ValidationError(
                {"status": "An opportunity is published when a college approves its invitation."}
            )
        company = self.context["request"].user.recruiter_profile.company
        colleges = attrs.get("target_colleges")
        if colleges is None and self.instance:
            colleges = list(self.instance.target_colleges.all())
        colleges = colleges or []

        verified_ids = set(
            CompanyCollegePartnership.objects.filter(
                company=company,
                status=CompanyCollegePartnership.Status.VERIFIED,
            ).values_list("college_id", flat=True)
        )
        unverified = [college.name for college in colleges if college.id not in verified_ids]
        if unverified:
            raise serializers.ValidationError(
                {"target_college_ids": f"Your company is not approved to recruit at: {', '.join(unverified)}."}
            )

        programs = attrs.get("eligible_programs")
        if programs is None and self.instance:
            programs = list(self.instance.eligible_programs.all())
        college_ids = {college.id for college in colleges}
        invalid_programs = [program.branch for program in (programs or []) if program.college_id not in college_ids]
        if invalid_programs:
            raise serializers.ValidationError(
                {"eligible_program_ids": "Every eligible program must belong to a targeted college."}
            )

        minimum = attrs.get("compensation_min", getattr(self.instance, "compensation_min", None))
        maximum = attrs.get("compensation_max", getattr(self.instance, "compensation_max", None))
        if minimum is not None and maximum is not None and maximum < minimum:
            raise serializers.ValidationError(
                {"compensation_max": "Maximum compensation cannot be below the minimum."}
            )

        year_from = attrs.get("graduation_year_from", getattr(self.instance, "graduation_year_from", None))
        year_to = attrs.get("graduation_year_to", getattr(self.instance, "graduation_year_to", None))
        if year_from and year_to and year_to < year_from:
            raise serializers.ValidationError(
                {"graduation_year_to": "Ending graduation year cannot be before the starting year."}
            )

        deadline = attrs.get("application_deadline", getattr(self.instance, "application_deadline", None))
        target_status = attrs.get("status", getattr(self.instance, "status", Opportunity.Status.DRAFT))
        if target_status == Opportunity.Status.PUBLISHED and not colleges:
            raise serializers.ValidationError(
                {"status": "Send this opportunity to at least one approved college before publishing."}
            )
        if not self.instance and target_status not in {
            Opportunity.Status.DRAFT,
            Opportunity.Status.PUBLISHED,
        }:
            raise serializers.ValidationError(
                {"status": "A new opportunity must be saved as a draft or published."}
            )
        if target_status == Opportunity.Status.PUBLISHED and deadline and deadline < date.today():
            raise serializers.ValidationError(
                {"application_deadline": "A published opportunity must have a current or future deadline."}
            )

        if self.instance and "status" in attrs and attrs["status"] != self.instance.status:
            transitions = {
                Opportunity.Status.DRAFT: {Opportunity.Status.PUBLISHED, Opportunity.Status.CANCELLED},
                Opportunity.Status.PUBLISHED: {Opportunity.Status.CLOSED, Opportunity.Status.CANCELLED},
                Opportunity.Status.CLOSED: set(),
                Opportunity.Status.CANCELLED: set(),
            }
            if attrs["status"] not in transitions[self.instance.status]:
                raise serializers.ValidationError({"status": "This opportunity status change is not allowed."})
        return attrs

    @staticmethod
    def _resolve_skills(names):
        skills = []
        for name in names:
            skill = Skill.objects.filter(name__iexact=name).first()
            skills.append(skill or Skill.objects.create(name=name))
        return skills

    @transaction.atomic
    def create(self, validated_data):
        colleges = validated_data.pop("target_colleges", [])
        programs = validated_data.pop("eligible_programs", [])
        skill_names = validated_data.pop("required_skill_names", [])
        if validated_data.get("status") == Opportunity.Status.PUBLISHED:
            validated_data["published_at"] = timezone.now()
        opportunity = Opportunity.objects.create(**validated_data)
        opportunity.target_colleges.set(colleges)
        opportunity.eligible_programs.set(programs)
        opportunity.required_skills.set(self._resolve_skills(skill_names))
        return opportunity

    @transaction.atomic
    def update(self, instance, validated_data):
        colleges = validated_data.pop("target_colleges", None)
        programs = validated_data.pop("eligible_programs", None)
        skill_names = validated_data.pop("required_skill_names", None)
        review_fields = {
            "title", "opportunity_type", "description", "responsibilities", "qualifications",
            "location", "work_mode", "openings", "compensation_min", "compensation_max",
            "compensation_period", "application_deadline", "min_cgpa", "max_active_backlogs",
            "graduation_year_from", "graduation_year_to",
        }
        requires_review = any(
            field in validated_data and validated_data[field] != getattr(instance, field)
            for field in review_fields
        )
        if skill_names is not None:
            existing_skills = {name.casefold() for name in instance.required_skills.values_list("name", flat=True)}
            requires_review = requires_review or existing_skills != {name.casefold() for name in skill_names}
        if validated_data.get("status") == Opportunity.Status.PUBLISHED and not instance.published_at:
            validated_data["published_at"] = timezone.now()
        instance = super().update(instance, validated_data)
        if colleges is not None:
            instance.target_colleges.set(colleges)
        if programs is not None:
            instance.eligible_programs.set(programs)
        if skill_names is not None:
            instance.required_skills.set(self._resolve_skills(skill_names))
        if requires_review:
            invitations = instance.college_invitations.exclude(
                status=OpportunityCollegeInvitation.Status.WITHDRAWN
            ).select_related("college")
            colleges_to_notify = [invitation.college for invitation in invitations]
            invitations.update(
                status=OpportunityCollegeInvitation.Status.PENDING,
                review_note="",
                reviewed_by=None,
                reviewed_at=None,
            )
            sync_approved_opportunity_audience(instance)
            for college in colleges_to_notify:
                notify_college_admins(
                    college=college,
                    category=Notification.Category.COMPANY,
                    title="Updated opportunity requires review",
                    message=f"{instance.company.name} updated “{instance.title}”. Please review it again.",
                    link="/admin/opportunity-requests",
                )
        return instance


class StudentOpportunitySerializer(OpportunitySerializer):
    is_eligible = serializers.SerializerMethodField()
    eligibility_reasons = serializers.SerializerMethodField()
    matched_skills = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta(OpportunitySerializer.Meta):
        fields = OpportunitySerializer.Meta.fields + (
            "is_eligible", "eligibility_reasons", "matched_skills",
            "is_saved",
        )
        read_only_fields = OpportunitySerializer.Meta.fields

    def _eligibility(self, opportunity):
        reasons = get_eligibility_reasons(
            opportunity,
            self.context["request"].user.student_profile,
        )
        from placements.services import get_college_policy_blockers

        reasons.extend(
            get_college_policy_blockers(self.context["request"].user.student_profile)
        )
        return reasons

    @extend_schema_field(serializers.BooleanField())
    def get_is_eligible(self, opportunity):
        return not self._eligibility(opportunity)

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_eligibility_reasons(self, opportunity):
        return self._eligibility(opportunity)

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_matched_skills(self, opportunity):
        student_skills = {
            name.casefold()
            for name in self.context["request"].user.student_profile.skills.values_list("skill__name", flat=True)
        }
        return [skill.name for skill in opportunity.required_skills.all() if skill.name.casefold() in student_skills]

    @extend_schema_field(serializers.BooleanField())
    def get_is_saved(self, opportunity):
        student_id = self.context["request"].user.student_profile.id
        return any(bookmark.student_id == student_id for bookmark in opportunity.bookmarks.all())


class RecommendedOpportunitySerializer(StudentOpportunitySerializer):
    match_score = serializers.IntegerField(read_only=True)
    match_reasons = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta(StudentOpportunitySerializer.Meta):
        fields = StudentOpportunitySerializer.Meta.fields + ("match_score", "match_reasons")


class OpportunityBookmarkStateSerializer(serializers.Serializer):
    opportunity_id = serializers.IntegerField(read_only=True)
    is_saved = serializers.BooleanField(read_only=True)


class OpportunityCollegeShareSerializer(serializers.Serializer):
    college_ids = serializers.PrimaryKeyRelatedField(
        source="colleges",
        queryset=College.objects.filter(is_active=True),
        many=True,
        allow_empty=False,
    )
    eligible_program_ids = serializers.PrimaryKeyRelatedField(
        source="programs",
        queryset=AcademicProgram.objects.filter(is_active=True, college__is_active=True),
        many=True,
        required=False,
    )
    recruiter_message = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    def validate(self, attrs):
        opportunity = self.context["opportunity"]
        if opportunity.status not in {Opportunity.Status.DRAFT, Opportunity.Status.PUBLISHED}:
            raise serializers.ValidationError("Only a draft or published opportunity can be sent to colleges.")
        colleges = attrs["colleges"]
        verified_ids = set(
            CompanyCollegePartnership.objects.filter(
                company=opportunity.company,
                status=CompanyCollegePartnership.Status.VERIFIED,
            ).values_list("college_id", flat=True)
        )
        unverified = [college.name for college in colleges if college.id not in verified_ids]
        if unverified:
            raise serializers.ValidationError(
                {"college_ids": f"Your company is not approved to recruit at: {', '.join(unverified)}."}
            )
        college_ids = {college.id for college in colleges}
        if any(program.college_id not in college_ids for program in attrs.get("programs", [])):
            raise serializers.ValidationError(
                {"eligible_program_ids": "Every eligible program must belong to a selected college."}
            )
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        opportunity = self.context["opportunity"]
        programs = self.validated_data.get("programs", [])
        message = self.validated_data.get("recruiter_message", "")
        for college in self.validated_data["colleges"]:
            invitation, created = OpportunityCollegeInvitation.objects.get_or_create(
                opportunity=opportunity,
                college=college,
                defaults={
                    "submitted_by": self.context["request"].user,
                    "recruiter_message": message,
                },
            )
            if not created:
                if invitation.status == OpportunityCollegeInvitation.Status.APPROVED:
                    continue
                invitation.status = OpportunityCollegeInvitation.Status.PENDING
                invitation.submitted_by = self.context["request"].user
                invitation.recruiter_message = message
                invitation.review_note = ""
                invitation.reviewed_by = None
                invitation.reviewed_at = None
                invitation.submitted_at = timezone.now()
                invitation.save(update_fields=(
                    "status", "submitted_by", "recruiter_message", "review_note",
                    "reviewed_by", "reviewed_at", "submitted_at", "updated_at",
                ))
            invitation.eligible_programs.set(
                program for program in programs if program.college_id == college.id
            )
            if invitation.status == OpportunityCollegeInvitation.Status.PENDING:
                notify_college_admins(
                    college=college,
                    category=Notification.Category.COMPANY,
                    title="Opportunity awaiting review",
                    message=f"{opportunity.company.name} submitted “{opportunity.title}” for your approval.",
                    link="/admin/opportunity-requests",
                )
        return opportunity


class CollegeOpportunitySummarySerializer(serializers.ModelSerializer):
    company = CompanySummarySerializer(read_only=True)
    opportunity_type_display = serializers.CharField(source="get_opportunity_type_display", read_only=True)
    work_mode_display = serializers.CharField(source="get_work_mode_display", read_only=True)
    required_skills = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    class Meta:
        model = Opportunity
        fields = (
            "id", "company", "title", "opportunity_type", "opportunity_type_display",
            "description", "responsibilities", "qualifications", "location", "work_mode",
            "work_mode_display", "openings", "compensation_min", "compensation_max",
            "compensation_period", "application_deadline", "min_cgpa", "max_active_backlogs",
            "graduation_year_from", "graduation_year_to", "required_skills", "status",
        )


class CollegeOpportunityInvitationSerializer(serializers.ModelSerializer):
    opportunity = CollegeOpportunitySummarySerializer(read_only=True)
    college = CollegeSerializer(read_only=True)
    eligible_programs = AcademicProgramSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = OpportunityCollegeInvitation
        fields = (
            "id", "opportunity", "college", "eligible_programs", "status", "status_display",
            "recruiter_message", "review_note", "submitted_at", "reviewed_at", "updated_at",
        )
        read_only_fields = (
            "id", "opportunity", "college", "eligible_programs", "status", "status_display",
            "recruiter_message", "review_note", "submitted_at", "reviewed_at", "updated_at",
        )


class CollegeOpportunityReviewSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=(
        OpportunityCollegeInvitation.Status.APPROVED,
        OpportunityCollegeInvitation.Status.REJECTED,
    ))

    class Meta:
        model = OpportunityCollegeInvitation
        fields = ("status", "review_note")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if "status" not in attrs:
            raise serializers.ValidationError({"status": "Choose approve or reject."})
        if self.instance.opportunity.status in {
            Opportunity.Status.CLOSED,
            Opportunity.Status.CANCELLED,
        }:
            raise serializers.ValidationError("A closed or cancelled opportunity cannot be reviewed.")
        if attrs["status"] == OpportunityCollegeInvitation.Status.REJECTED and not attrs.get(
            "review_note", self.instance.review_note
        ).strip():
            raise serializers.ValidationError({"review_note": "Explain why the opportunity is rejected."})
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.review_note = validated_data.get("review_note", "")
        instance.reviewed_by = self.context["request"].user
        instance.reviewed_at = timezone.now()
        instance.save(update_fields=(
            "status", "review_note", "reviewed_by", "reviewed_at", "updated_at",
        ))
        sync_approved_opportunity_audience(instance.opportunity)
        notify_company_recruiters(
            company=instance.opportunity.company,
            category=Notification.Category.COMPANY,
            title=f"Opportunity {instance.get_status_display().lower()}",
            message=f"{instance.college.name} {instance.get_status_display().lower()} “{instance.opportunity.title}”.",
            link="/recruiter/opportunities",
        )
        return instance
