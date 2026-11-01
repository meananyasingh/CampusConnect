from django.utils import timezone
from rest_framework import serializers

from colleges.models import AcademicProgram, College
from colleges.serializers import AcademicProgramSerializer, CollegeSerializer
from companies.models import CompanyCollegePartnership
from companies.serializers import CompanySummarySerializer
from opportunities.models import Opportunity
from placements.models import PlacementDrive

from .models import Announcement


class RelatedOpportunitySerializer(serializers.ModelSerializer):
    company = CompanySummarySerializer(read_only=True)

    class Meta:
        model = Opportunity
        fields = ("id", "title", "company")


class RelatedDriveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlacementDrive
        fields = ("id", "title", "start_date", "end_date")


class AnnouncementSerializer(serializers.ModelSerializer):
    college = CollegeSerializer(read_only=True)
    college_id = serializers.PrimaryKeyRelatedField(source="college", queryset=College.objects.filter(is_active=True), write_only=True, required=False)
    company = CompanySummarySerializer(read_only=True)
    target_programs = AcademicProgramSerializer(many=True, read_only=True)
    target_program_ids = serializers.PrimaryKeyRelatedField(source="target_programs", queryset=AcademicProgram.objects.filter(is_active=True), many=True, write_only=True, required=False)
    related_opportunity = RelatedOpportunitySerializer(read_only=True)
    related_opportunity_id = serializers.PrimaryKeyRelatedField(source="related_opportunity", queryset=Opportunity.objects.all(), write_only=True, required=False, allow_null=True)
    related_drive = RelatedDriveSerializer(read_only=True)
    related_drive_id = serializers.PrimaryKeyRelatedField(source="related_drive", queryset=PlacementDrive.objects.all(), write_only=True, required=False, allow_null=True)
    announcement_type_display = serializers.CharField(source="get_announcement_type_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    approval_status_display = serializers.CharField(source="get_approval_status_display", read_only=True)
    created_by_role = serializers.CharField(source="created_by.role", read_only=True)
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = (
            "id", "college", "college_id", "company", "title", "body",
            "announcement_type", "announcement_type_display", "priority", "priority_display",
            "target_programs", "target_program_ids", "target_graduation_years",
            "related_opportunity", "related_opportunity_id", "related_drive", "related_drive_id",
            "publish_at", "expires_at", "is_pinned", "is_archived", "approval_status",
            "approval_status_display", "review_note", "created_by_role", "is_read",
            "reviewed_at", "created_at", "updated_at",
        )
        read_only_fields = ("id", "company", "created_by_role", "is_read", "reviewed_at", "created_at", "updated_at")

    def get_is_read(self, announcement) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and any(receipt.user_id == request.user.id for receipt in announcement.read_receipts.all())
        )

    def validate_target_graduation_years(self, years):
        if not isinstance(years, list) or any(not isinstance(year, int) or year < 2000 or year > 2100 for year in years):
            raise serializers.ValidationError("Use a list of valid graduation years.")
        return sorted(set(years))

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context["request"]
        role = request.user.role
        if role == "ADMIN":
            profile = getattr(request.user, "college_admin_profile", None)
            if profile is None:
                raise serializers.ValidationError("Configure a college admin profile first.")
            college = profile.college
            if self.instance and "approval_status" in attrs and attrs["approval_status"] != self.instance.approval_status:
                raise serializers.ValidationError({"approval_status": "Use the announcement review action."})
        else:
            company = request.user.recruiter_profile.company
            college = attrs.get("college", getattr(self.instance, "college", None))
            if not college or not CompanyCollegePartnership.objects.filter(
                company=company, college=college, status=CompanyCollegePartnership.Status.VERIFIED,
            ).exists():
                raise serializers.ValidationError({"college_id": "Select a college that approved your company."})
            if "approval_status" in attrs and attrs["approval_status"] != Announcement.ApprovalStatus.PENDING:
                raise serializers.ValidationError({"approval_status": "Only the college can review an announcement."})

        programs = attrs.get("target_programs")
        if programs is None and self.instance:
            programs = list(self.instance.target_programs.all())
        if any(program.college_id != college.id for program in (programs or [])):
            raise serializers.ValidationError({"target_program_ids": "Every target program must belong to the selected college."})
        opportunity = attrs.get("related_opportunity", getattr(self.instance, "related_opportunity", None))
        if opportunity:
            if not opportunity.target_colleges.filter(pk=college.id).exists():
                raise serializers.ValidationError({"related_opportunity_id": "This opportunity was not sent to the selected college."})
            if role == "RECRUITER" and opportunity.company_id != request.user.recruiter_profile.company_id:
                raise serializers.ValidationError({"related_opportunity_id": "Select one of your company's opportunities."})
        drive = attrs.get("related_drive", getattr(self.instance, "related_drive", None))
        if drive and drive.college_id != college.id:
            raise serializers.ValidationError({"related_drive_id": "This drive belongs to another college."})
        if drive and role == "RECRUITER" and not drive.opportunities.filter(
            company=request.user.recruiter_profile.company,
        ).exists():
            raise serializers.ValidationError({"related_drive_id": "Your company is not participating in this drive."})
        publish_at = attrs.get("publish_at", getattr(self.instance, "publish_at", None))
        expires_at = attrs.get("expires_at", getattr(self.instance, "expires_at", None))
        if expires_at and publish_at and expires_at <= publish_at:
            raise serializers.ValidationError({"expires_at": "Expiry must be after publication."})
        return attrs


class AnnouncementReviewSerializer(serializers.Serializer):
    approval_status = serializers.ChoiceField(choices=(Announcement.ApprovalStatus.APPROVED, Announcement.ApprovalStatus.REJECTED))
    review_note = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate(self, attrs):
        if self.context["announcement"].approval_status != Announcement.ApprovalStatus.PENDING:
            raise serializers.ValidationError("This announcement has already been reviewed.")
        return attrs
