from django.urls import reverse
from rest_framework import serializers

from colleges.serializers import AcademicProgramSerializer, CollegeSerializer
from students.models import StudentProfile
from students.services import calculate_profile_completion

from .models import TalentPool, TalentPoolMember
from .services import recruiter_can_access_student


class CandidateSkillSerializer(serializers.Serializer):
    name = serializers.CharField(source="skill.name")
    proficiency = serializers.CharField()
    proficiency_display = serializers.CharField(source="get_proficiency_display")
    years_experience = serializers.DecimalField(max_digits=4, decimal_places=1)


class CandidateSummarySerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source="user.first_name")
    last_name = serializers.CharField(source="user.last_name")
    college = CollegeSerializer(read_only=True)
    program = AcademicProgramSerializer(read_only=True)
    skills = CandidateSkillSerializer(many=True, read_only=True)
    profile_completion = serializers.SerializerMethodField()
    has_primary_resume = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = (
            "id", "first_name", "last_name", "college", "program", "graduation_year",
            "profile_picture", "location", "career_objective", "preferred_job_role",
            "preferred_locations", "cgpa", "active_backlogs", "skills",
            "profile_completion", "has_primary_resume",
        )

    def get_profile_completion(self, instance) -> int:
        return calculate_profile_completion(instance)["percentage"]

    def get_has_primary_resume(self, instance) -> bool:
        return any(resume.is_primary for resume in instance.resumes.all())


class CandidateDetailSerializer(CandidateSummarySerializer):
    email = serializers.EmailField(source="user.email")
    projects = serializers.SerializerMethodField()
    certifications = serializers.SerializerMethodField()
    experiences = serializers.SerializerMethodField()
    primary_resume = serializers.SerializerMethodField()

    class Meta(CandidateSummarySerializer.Meta):
        fields = CandidateSummarySerializer.Meta.fields + (
            "email", "linkedin_url", "github_url", "portfolio_url", "projects",
            "certifications", "experiences", "primary_resume",
        )

    def get_projects(self, instance) -> list[dict]:
        return list(instance.projects.values(
            "id", "title", "description", "technologies", "github_url", "live_url",
            "start_date", "end_date", "is_ongoing",
        ))

    def get_certifications(self, instance) -> list[dict]:
        return list(instance.certifications.values(
            "id", "name", "issuing_organization", "credential_id", "credential_url",
            "issue_date", "expiry_date",
        ))

    def get_experiences(self, instance) -> list[dict]:
        return list(instance.experiences.values(
            "id", "organization", "role", "employment_type", "location", "description",
            "start_date", "end_date", "is_current",
        ))

    def get_primary_resume(self, instance) -> dict | None:
        resume = next((item for item in instance.resumes.all() if item.is_primary), None)
        if resume is None:
            return None
        request = self.context.get("request")
        url = reverse("talent-candidate-resume", args=(instance.pk,))
        return {
            "id": resume.id,
            "title": resume.title,
            "original_filename": resume.original_filename,
            "updated_at": resume.updated_at,
            "download_url": request.build_absolute_uri(url) if request else url,
        }


class TalentPoolMemberSerializer(serializers.ModelSerializer):
    student = CandidateSummarySerializer(read_only=True)
    student_id = serializers.PrimaryKeyRelatedField(
        source="student",
        queryset=StudentProfile.objects.all(),
        write_only=True,
    )
    added_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TalentPoolMember
        fields = (
            "id", "student", "student_id", "private_notes", "added_by_name",
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "student", "added_by_name", "created_at", "updated_at")

    def get_added_by_name(self, instance) -> str:
        return instance.added_by.get_full_name() or instance.added_by.email

    def validate_student_id(self, student):
        if not recruiter_can_access_student(self.context["request"].user, student):
            raise serializers.ValidationError(
                "This student is not discoverable through one of your verified colleges."
            )
        return student

    def validate(self, attrs):
        attrs = super().validate(attrs)
        pool = self.context.get("pool")
        student = attrs.get("student")
        if pool and student and pool.members.filter(student=student).exists():
            raise serializers.ValidationError({"student_id": "This student is already in the pool."})
        return attrs


class TalentPoolSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)
    members = TalentPoolMemberSerializer(many=True, read_only=True)

    class Meta:
        model = TalentPool
        fields = (
            "id", "name", "description", "member_count", "members", "created_at", "updated_at",
        )
        read_only_fields = ("id", "member_count", "members", "created_at", "updated_at")

    def validate_name(self, value):
        value = " ".join(value.split())
        company = self.context["request"].user.recruiter_profile.company
        duplicate = TalentPool.objects.filter(company=company, name__iexact=value)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError("Your company already has a talent pool with this name.")
        return value
