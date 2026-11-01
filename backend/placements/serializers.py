from rest_framework import serializers

from applications.models import Application, InterviewSchedule
from applications.serializers import ApplicationSerializer, ApplicationOpportunitySerializer
from companies.models import CompanyCollegePartnership
from opportunities.models import Opportunity
from notifications.models import Notification
from notifications.services import create_notification, notify_college_admins

from .models import CollegePlacementPolicy, PlacementDrive, PlacementRecord


class CollegeDashboardSerializer(serializers.Serializer):
    college = serializers.DictField(read_only=True)
    total_students = serializers.IntegerField(read_only=True)
    total_recruiters = serializers.IntegerField(read_only=True)
    verified_companies = serializers.IntegerField(read_only=True)
    active_opportunities = serializers.IntegerField(read_only=True)
    total_applications = serializers.IntegerField(read_only=True)
    shortlisted_candidates = serializers.IntegerField(read_only=True)
    upcoming_interviews = serializers.IntegerField(read_only=True)
    placed_students = serializers.IntegerField(read_only=True)
    placement_percentage = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)
    average_package = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, allow_null=True)
    highest_package = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True, allow_null=True)


class CollegePlacementPolicySerializer(serializers.ModelSerializer):
    college = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = CollegePlacementPolicy
        fields = (
            "id", "college", "applications_enabled", "require_verified_documents",
            "minimum_profile_completion", "minimum_cgpa", "max_active_backlogs",
            "student_message", "updated_by_name", "created_at", "updated_at",
        )
        read_only_fields = ("id", "college", "updated_by_name", "created_at", "updated_at")

    def get_college(self, policy) -> dict:
        return {"id": policy.college_id, "name": policy.college.name, "code": policy.college.code}

    def get_updated_by_name(self, policy) -> str:
        if not policy.updated_by:
            return ""
        return policy.updated_by.get_full_name() or policy.updated_by.email

    def validate(self, attrs):
        attrs = super().validate(attrs)
        minimum = attrs.get("minimum_cgpa", getattr(self.instance, "minimum_cgpa", None))
        if minimum is not None and minimum > 10:
            raise serializers.ValidationError({"minimum_cgpa": "CGPA cannot exceed 10."})
        return attrs


class StudentPlacementReadinessSerializer(serializers.Serializer):
    is_ready = serializers.BooleanField()
    blockers = serializers.ListField(child=serializers.CharField())
    profile_completion = serializers.IntegerField()
    document_verification = serializers.DictField()
    policy = serializers.DictField()


class PlacementDriveOpportunitySerializer(ApplicationOpportunitySerializer):
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta(ApplicationOpportunitySerializer.Meta):
        fields = ApplicationOpportunitySerializer.Meta.fields + ("status", "status_display")


class PlacementDriveSerializer(serializers.ModelSerializer):
    college = serializers.SerializerMethodField()
    opportunities = PlacementDriveOpportunitySerializer(many=True, read_only=True)
    opportunity_ids = serializers.PrimaryKeyRelatedField(
        source="opportunities",
        queryset=Opportunity.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    company_count = serializers.SerializerMethodField()
    opportunity_count = serializers.SerializerMethodField()
    application_count = serializers.SerializerMethodField()
    interview_count = serializers.SerializerMethodField()
    selected_count = serializers.SerializerMethodField()

    class Meta:
        model = PlacementDrive
        fields = (
            "id", "college", "title", "description", "start_date", "end_date",
            "venue", "status", "status_display", "opportunities", "opportunity_ids",
            "company_count", "opportunity_count", "application_count", "interview_count",
            "selected_count", "created_at", "updated_at",
        )
        read_only_fields = ("id", "college", "created_at", "updated_at")

    def get_college(self, drive) -> dict:
        return {"id": drive.college_id, "name": drive.college.name, "code": drive.college.code}

    def get_company_count(self, drive) -> int:
        return drive.opportunities.values("company_id").distinct().count()

    def get_opportunity_count(self, drive) -> int:
        return drive.opportunities.count()

    def get_application_count(self, drive) -> int:
        return Application.objects.filter(
            opportunity__placement_drives=drive,
            student__college=drive.college,
        ).count()

    def get_interview_count(self, drive) -> int:
        return InterviewSchedule.objects.filter(
            application__opportunity__placement_drives=drive,
            application__student__college=drive.college,
        ).count()

    def get_selected_count(self, drive) -> int:
        return Application.objects.filter(
            opportunity__placement_drives=drive,
            student__college=drive.college,
            status=Application.Status.SELECTED,
        ).count()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context["request"]
        admin_profile = getattr(request.user, "college_admin_profile", None)
        if admin_profile is None:
            raise serializers.ValidationError("Configure a college admin profile before managing drives.")
        opportunities = attrs.get("opportunities")
        if opportunities is None and self.instance:
            opportunities = list(self.instance.opportunities.all())
        opportunities = opportunities or []
        invalid = [
            item.title for item in opportunities
            if item.status not in (Opportunity.Status.PUBLISHED, Opportunity.Status.CLOSED)
            or not item.target_colleges.filter(pk=admin_profile.college_id).exists()
            or not CompanyCollegePartnership.objects.filter(
                company=item.company,
                college=admin_profile.college,
                status=CompanyCollegePartnership.Status.VERIFIED,
            ).exists()
        ]
        if invalid:
            raise serializers.ValidationError({
                "opportunity_ids": f"These opportunities are not approved for your college: {', '.join(invalid)}."
            })
        if self.instance and "opportunities" in attrs and self.instance.status not in (
            PlacementDrive.Status.DRAFT,
            PlacementDrive.Status.UPCOMING,
        ):
            raise serializers.ValidationError({
                "opportunity_ids": "Opportunities cannot be changed after a drive starts."
            })
        start_date = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be before the start date."})
        target_status = attrs.get("status", getattr(self.instance, "status", PlacementDrive.Status.DRAFT))
        if target_status != PlacementDrive.Status.DRAFT and not opportunities:
            raise serializers.ValidationError({"status": "Add at least one opportunity before publishing the drive."})
        if self.instance and "status" in attrs and target_status != self.instance.status:
            transitions = {
                PlacementDrive.Status.DRAFT: {PlacementDrive.Status.UPCOMING, PlacementDrive.Status.CANCELLED},
                PlacementDrive.Status.UPCOMING: {PlacementDrive.Status.ONGOING, PlacementDrive.Status.CANCELLED},
                PlacementDrive.Status.ONGOING: {PlacementDrive.Status.COMPLETED, PlacementDrive.Status.CANCELLED},
                PlacementDrive.Status.COMPLETED: set(),
                PlacementDrive.Status.CANCELLED: set(),
            }
            if target_status not in transitions[self.instance.status]:
                raise serializers.ValidationError({"status": "This placement-drive status change is not allowed."})
        return attrs

    def create(self, validated_data):
        opportunities = validated_data.pop("opportunities", [])
        admin_profile = self.context["request"].user.college_admin_profile
        drive = PlacementDrive.objects.create(
            college=admin_profile.college,
            created_by=self.context["request"].user,
            **validated_data,
        )
        drive.opportunities.set(opportunities)
        return drive

    def update(self, instance, validated_data):
        opportunities = validated_data.pop("opportunities", None)
        drive = super().update(instance, validated_data)
        if opportunities is not None:
            drive.opportunities.set(opportunities)
        return drive


class PlacementRecordSerializer(serializers.ModelSerializer):
    application = ApplicationSerializer(read_only=True)
    application_id = serializers.PrimaryKeyRelatedField(
        source="application",
        queryset=Application.objects.select_related("student", "opportunity"),
        write_only=True,
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    college_name = serializers.CharField(source="college.name", read_only=True)

    class Meta:
        model = PlacementRecord
        fields = (
            "id", "application", "application_id", "college_name", "annual_package",
            "offer_date", "joining_date", "status", "status_display", "student_message",
            "admin_notes", "created_at", "updated_at",
        )
        read_only_fields = ("id", "college_name", "created_at", "updated_at")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance
        application = attrs.get("application", getattr(instance, "application", None))
        admin_profile = getattr(self.context["request"].user, "college_admin_profile", None)
        if admin_profile is None:
            raise serializers.ValidationError("Configure a college admin profile before managing placements.")
        if application.student.college_id != admin_profile.college_id:
            raise serializers.ValidationError({"application_id": "This student belongs to another college."})
        if application.status != Application.Status.SELECTED:
            raise serializers.ValidationError({"application_id": "Only selected applications can be recorded."})
        if instance and "application" in attrs and application.id != instance.application_id:
            raise serializers.ValidationError({"application_id": "A placement record cannot be moved to another application."})
        if not instance and PlacementRecord.objects.filter(application=application).exists():
            raise serializers.ValidationError({"application_id": "A placement record already exists for this application."})
        if not instance and attrs.get("status", PlacementRecord.Status.OFFERED) != PlacementRecord.Status.OFFERED:
            raise serializers.ValidationError({"status": "A new placement record must begin as an issued offer."})
        offer_date = attrs.get("offer_date", getattr(instance, "offer_date", None))
        joining_date = attrs.get("joining_date", getattr(instance, "joining_date", None))
        if joining_date and offer_date and joining_date < offer_date:
            raise serializers.ValidationError({"joining_date": "Joining date cannot be before the offer date."})
        if instance and "status" in attrs and attrs["status"] != instance.status:
            transitions = {
                PlacementRecord.Status.OFFERED: {
                    PlacementRecord.Status.ACCEPTED,
                    PlacementRecord.Status.DECLINED,
                    PlacementRecord.Status.CANCELLED,
                },
                PlacementRecord.Status.ACCEPTED: {
                    PlacementRecord.Status.JOINED,
                    PlacementRecord.Status.CANCELLED,
                },
                PlacementRecord.Status.DECLINED: set(),
                PlacementRecord.Status.JOINED: set(),
                PlacementRecord.Status.CANCELLED: set(),
            }
            if attrs["status"] not in transitions[instance.status]:
                raise serializers.ValidationError({"status": "This placement status change is not allowed."})
        return attrs

    def create(self, validated_data):
        admin_profile = self.context["request"].user.college_admin_profile
        placement = PlacementRecord.objects.create(
            college=admin_profile.college,
            verified_by=self.context["request"].user,
            **validated_data,
        )
        create_notification(
            recipient=placement.application.student.user,
            category=Notification.Category.PLACEMENT,
            title="Placement offer recorded",
            message=f"Your offer from {placement.application.opportunity.company.name} is ready for review.",
            link="/student/placements",
        )
        return placement

    def update(self, instance, validated_data):
        previous_status = instance.status
        placement = super().update(instance, validated_data)
        if placement.status != previous_status:
            create_notification(
                recipient=placement.application.student.user,
                category=Notification.Category.PLACEMENT,
                title=f"Placement {placement.get_status_display().lower()}",
                message=f"Your placement record for {placement.application.opportunity.company.name} was updated.",
                link="/student/placements",
            )
        return placement


class StudentPlacementRecordSerializer(serializers.ModelSerializer):
    application = ApplicationSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    college_name = serializers.CharField(source="college.name", read_only=True)

    class Meta:
        model = PlacementRecord
        fields = (
            "id", "application", "college_name", "annual_package", "offer_date",
            "joining_date", "status", "status_display", "student_message",
            "created_at", "updated_at",
        )


class StudentPlacementDecisionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=(
        PlacementRecord.Status.ACCEPTED,
        PlacementRecord.Status.DECLINED,
    ))

    def validate_status(self, status):
        if self.context["placement"].status != PlacementRecord.Status.OFFERED:
            raise serializers.ValidationError("A decision has already been recorded for this offer.")
        return status

    def save(self, **kwargs):
        placement = self.context["placement"]
        placement.status = self.validated_data["status"]
        placement.save(update_fields=("status", "updated_at"))
        notify_college_admins(
            college=placement.college,
            category=Notification.Category.PLACEMENT,
            title=f"Student {placement.get_status_display().lower()}",
            message=f"A student responded to the {placement.application.opportunity.company.name} placement offer.",
            link="/admin/placements",
        )
        return placement
