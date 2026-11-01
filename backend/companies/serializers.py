from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserSerializer
from colleges.models import College
from colleges.serializers import CollegeSerializer
from notifications.models import Notification
from notifications.services import notify_college_admins, notify_company_recruiters

from .models import Company, CompanyCollegePartnership, RecruiterProfile


class PartnershipSummarySerializer(serializers.ModelSerializer):
    college = CollegeSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CompanyCollegePartnership
        fields = ("id", "college", "status", "status_display", "review_note", "reviewed_at")


class RecruiterPartnershipSerializer(PartnershipSummarySerializer):
    college_id = serializers.PrimaryKeyRelatedField(
        source="college",
        queryset=College.objects.filter(is_active=True),
        write_only=True,
    )

    class Meta(PartnershipSummarySerializer.Meta):
        fields = PartnershipSummarySerializer.Meta.fields + ("college_id",)
        read_only_fields = ("id", "college", "status", "status_display", "review_note", "reviewed_at")

    def validate_college_id(self, college):
        company = self.context["request"].user.recruiter_profile.company
        if CompanyCollegePartnership.objects.filter(company=company, college=college).exists():
            raise serializers.ValidationError("Your company has already sent a recruitment request to this college.")
        return college

    def create(self, validated_data):
        partnership = super().create(validated_data)
        notify_college_admins(
            college=partnership.college,
            category=Notification.Category.COMPANY,
            title="New company recruitment request",
            message=f"{partnership.company.name} wants to recruit students from your college.",
            link="/admin/companies",
        )
        return partnership


class CompanySerializer(serializers.ModelSerializer):
    partnerships = PartnershipSummarySerializer(source="college_partnerships", many=True, read_only=True)

    class Meta:
        model = Company
        fields = (
            "id", "name", "slug", "industry", "website", "contact_email", "phone",
            "headquarters", "company_size", "description", "linkedin_url", "logo",
            "is_active", "partnerships", "created_at", "updated_at",
        )
        read_only_fields = ("id", "slug", "is_active", "partnerships", "created_at", "updated_at")

    def validate_name(self, value):
        name = " ".join(value.split())
        duplicate = Company.objects.filter(name__iexact=name)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError("A company with this name is already registered.")
        return name

    def validate_logo(self, value):
        if value and value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Company logo must not exceed 2 MB.")
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        content_type = getattr(value, "content_type", None)
        if value and content_type and content_type not in allowed_types:
            raise serializers.ValidationError("Use a JPEG, PNG, or WebP image.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        verification_fields = {"name", "website", "contact_email"}
        requires_review = any(
            field in validated_data and validated_data[field] != getattr(instance, field)
            for field in verification_fields
        )
        instance = super().update(instance, validated_data)
        if requires_review:
            instance.college_partnerships.exclude(
                status=CompanyCollegePartnership.Status.PENDING
            ).update(
                status=CompanyCollegePartnership.Status.PENDING,
                review_note="Company identity details changed; verification is required again.",
                reviewed_by=None,
                reviewed_at=None,
            )
            instance._prefetched_objects_cache = {}
        return instance


class RecruiterProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    first_name = serializers.CharField(source="user.first_name", write_only=True, required=False)
    last_name = serializers.CharField(source="user.last_name", write_only=True, required=False)

    class Meta:
        model = RecruiterProfile
        fields = (
            "id", "user", "company", "first_name", "last_name", "designation", "phone",
            "is_company_owner", "created_at", "updated_at",
        )
        read_only_fields = ("id", "user", "company", "is_company_owner", "created_at", "updated_at")

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        for field, value in user_data.items():
            setattr(instance.user, field, value.strip())
        if user_data:
            instance.user.save(update_fields=tuple(user_data))
        return super().update(instance, validated_data)


class CompanySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = (
            "id", "name", "slug", "industry", "website", "contact_email", "phone",
            "headquarters", "company_size", "description", "linkedin_url", "logo", "is_active",
        )


class PartnershipAdminSerializer(serializers.ModelSerializer):
    company = CompanySummarySerializer(read_only=True)
    college = CollegeSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CompanyCollegePartnership
        fields = (
            "id", "company", "college", "status", "status_display", "review_note",
            "reviewed_at", "created_at", "updated_at",
        )
        read_only_fields = ("id", "company", "college", "status_display", "reviewed_at", "created_at", "updated_at")

    def update(self, instance, validated_data):
        instance.reviewed_by = self.context["request"].user
        instance.reviewed_at = timezone.now()
        partnership = super().update(instance, validated_data)
        notify_company_recruiters(
            company=partnership.company,
            category=Notification.Category.COMPANY,
            title=f"College request {partnership.get_status_display().lower()}",
            message=f"{partnership.college.name} responded to your recruitment request.",
            link="/recruiter/company",
        )
        return partnership
