from datetime import date
from pathlib import Path

from django.db import transaction
from rest_framework import serializers

from accounts.serializers import UserSerializer
from colleges.serializers import AcademicProgramSerializer, CollegeSerializer

from .models import (
    Skill,
    StudentCertification,
    StudentExperience,
    StudentImportBatch,
    StudentProfile,
    StudentProject,
    StudentResume,
    StudentSkill,
)


class StudentImportBatchSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentImportBatch
        fields = (
            "id", "original_filename", "status", "status_display", "total_rows",
            "valid_rows", "invalid_rows", "imported_count", "rows",
            "created_by_name", "completed_at", "created_at",
        )
        read_only_fields = fields

    def get_created_by_name(self, batch) -> str:
        return batch.created_by.get_full_name() or batch.created_by.email


class StudentImportUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)


class StudentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    first_name = serializers.CharField(
        source="user.first_name",
        write_only=True,
        required=False,
        allow_blank=False,
    )
    last_name = serializers.CharField(
        source="user.last_name",
        write_only=True,
        required=False,
        allow_blank=False,
    )
    college = CollegeSerializer(read_only=True)
    program = AcademicProgramSerializer(read_only=True)

    class Meta:
        model = StudentProfile
        fields = (
            "id",
            "user",
            "first_name",
            "last_name",
            "college",
            "program",
            "enrollment_number",
            "graduation_year",
            "phone",
            "profile_picture",
            "date_of_birth",
            "location",
            "career_objective",
            "linkedin_url",
            "github_url",
            "portfolio_url",
            "preferred_job_role",
            "preferred_locations",
            "is_visible_to_recruiters",
            "cgpa",
            "tenth_percentage",
            "twelfth_percentage",
            "active_backlogs",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user",
            "college",
            "program",
            "enrollment_number",
            "graduation_year",
            "created_at",
            "updated_at",
        )

    def validate_date_of_birth(self, value):
        if value and value >= date.today():
            raise serializers.ValidationError("Date of birth must be in the past.")
        return value

    def validate_profile_picture(self, value):
        if value and value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Profile picture must not exceed 2 MB.")
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        content_type = getattr(value, "content_type", None)
        if value and content_type and content_type not in allowed_types:
            raise serializers.ValidationError("Use a JPEG, PNG, or WebP image.")
        return value

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        for attribute, value in user_data.items():
            setattr(instance.user, attribute, value.strip() if isinstance(value, str) else value)
        if user_data:
            instance.user.save(update_fields=tuple(user_data.keys()))
        return super().update(instance, validated_data)


class AdminStudentProfileSerializer(StudentProfileSerializer):
    account_is_active = serializers.BooleanField(source="user.is_active", required=False)
    activation_status = serializers.SerializerMethodField()
    activation_email_sent_at = serializers.DateTimeField(source="user.activation_email_sent_at", read_only=True)
    activation_email_count = serializers.IntegerField(source="user.activation_email_count", read_only=True)

    class Meta(StudentProfileSerializer.Meta):
        fields = StudentProfileSerializer.Meta.fields + (
            "account_is_active", "activation_status", "activation_email_sent_at",
            "activation_email_count",
        )
        read_only_fields = StudentProfileSerializer.Meta.read_only_fields

    def get_activation_status(self, profile) -> str:
        return "ACTIVATED" if profile.user.activated_at and profile.user.has_usable_password() else "PENDING"


class StudentOwnedSerializer(serializers.ModelSerializer):
    """Shared validation helpers for dated portfolio records."""

    date_pair = (None, None)
    current_field = None

    def validate(self, attrs):
        attrs = super().validate(attrs)
        start_field, end_field = self.date_pair
        if not start_field:
            return attrs

        start_date = attrs.get(start_field, getattr(self.instance, start_field, None))
        end_date = attrs.get(end_field, getattr(self.instance, end_field, None))
        is_current = (
            attrs.get(self.current_field, getattr(self.instance, self.current_field, False))
            if self.current_field
            else False
        )
        if is_current and end_date:
            raise serializers.ValidationError(
                {end_field: "Remove the end date when this entry is marked as current."}
            )
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                {end_field: "End date cannot be before the start date."}
            )
        return attrs


class StudentSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source="skill.name", max_length=80)
    proficiency_display = serializers.CharField(source="get_proficiency_display", read_only=True)

    class Meta:
        model = StudentSkill
        fields = (
            "id",
            "skill_name",
            "proficiency",
            "proficiency_display",
            "years_experience",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_skill_name(self, value):
        value = " ".join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError("Skill name must contain at least 2 characters.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        skill_name = attrs.get("skill", {}).get("name")
        if not skill_name:
            return attrs
        existing_skill = Skill.objects.filter(name__iexact=skill_name).first()
        student = self.context["request"].user.student_profile
        duplicate = StudentSkill.objects.filter(student=student, skill=existing_skill)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if existing_skill and duplicate.exists():
            raise serializers.ValidationError({"skill_name": "You already added this skill."})
        return attrs

    @staticmethod
    def _get_or_create_skill(skill_data):
        name = skill_data["name"]
        skill = Skill.objects.filter(name__iexact=name).first()
        return skill or Skill.objects.create(name=name)

    def create(self, validated_data):
        skill = self._get_or_create_skill(validated_data.pop("skill"))
        return StudentSkill.objects.create(skill=skill, **validated_data)

    def update(self, instance, validated_data):
        skill_data = validated_data.pop("skill", None)
        if skill_data:
            instance.skill = self._get_or_create_skill(skill_data)
        return super().update(instance, validated_data)


class StudentProjectSerializer(StudentOwnedSerializer):
    date_pair = ("start_date", "end_date")
    current_field = "is_ongoing"

    class Meta:
        model = StudentProject
        exclude = ("student",)
        read_only_fields = ("id", "created_at", "updated_at")


class StudentCertificationSerializer(StudentOwnedSerializer):
    date_pair = ("issue_date", "expiry_date")

    class Meta:
        model = StudentCertification
        exclude = ("student",)
        read_only_fields = ("id", "created_at", "updated_at")


class StudentExperienceSerializer(StudentOwnedSerializer):
    date_pair = ("start_date", "end_date")
    current_field = "is_current"
    employment_type_display = serializers.CharField(
        source="get_employment_type_display",
        read_only=True,
    )

    class Meta:
        model = StudentExperience
        exclude = ("student",)
        read_only_fields = ("id", "created_at", "updated_at")


class StudentResumeSerializer(serializers.ModelSerializer):
    file_url = serializers.FileField(source="file", read_only=True)

    class Meta:
        model = StudentResume
        fields = (
            "id",
            "title",
            "file",
            "file_url",
            "original_filename",
            "file_size",
            "is_primary",
            "created_at",
            "updated_at",
        )
        extra_kwargs = {"file": {"write_only": True}}
        read_only_fields = (
            "id",
            "file_url",
            "original_filename",
            "file_size",
            "created_at",
            "updated_at",
        )

    def validate_file(self, value):
        if self.instance:
            raise serializers.ValidationError("Upload a new resume version instead of replacing this file.")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Resume must not exceed 5 MB.")
        if Path(value.name).suffix.lower() != ".pdf":
            raise serializers.ValidationError("Resume must be a PDF file.")
        content_type = getattr(value, "content_type", None)
        if content_type and content_type != "application/pdf":
            raise serializers.ValidationError("Resume must be a PDF file.")
        signature = value.read(1024)
        value.seek(0)
        if b"%PDF-" not in signature:
            raise serializers.ValidationError("The uploaded file is not a valid PDF.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not self.instance and "file" not in attrs:
            raise serializers.ValidationError({"file": "Select a PDF resume to upload."})
        if self.instance and self.instance.is_primary and attrs.get("is_primary") is False:
            raise serializers.ValidationError(
                {"is_primary": "Choose another resume as primary instead."}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        student = validated_data["student"]
        uploaded_file = validated_data["file"]
        if not StudentResume.objects.filter(student=student).exists():
            validated_data["is_primary"] = True
        elif validated_data.get("is_primary"):
            StudentResume.objects.filter(student=student, is_primary=True).update(is_primary=False)
        validated_data["original_filename"] = Path(uploaded_file.name).name
        validated_data["file_size"] = uploaded_file.size
        return super().create(validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        if validated_data.get("is_primary"):
            StudentResume.objects.filter(
                student=instance.student,
                is_primary=True,
            ).exclude(pk=instance.pk).update(is_primary=False)
        return super().update(instance, validated_data)


class ProfileCompletionSectionSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    weight = serializers.IntegerField()
    percentage = serializers.IntegerField()
    score = serializers.IntegerField()
    missing = serializers.ListField(child=serializers.CharField())


class ProfileCompletionSerializer(serializers.Serializer):
    percentage = serializers.IntegerField()
    sections = ProfileCompletionSectionSerializer(many=True)
    missing = serializers.ListField(child=serializers.CharField())
