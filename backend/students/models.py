from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q


enrollment_number_validator = RegexValidator(
    regex=r"^[A-Za-z0-9][A-Za-z0-9/_-]{2,39}$",
    message="Use 3-40 letters, numbers, slashes, underscores, or hyphens.",
)

phone_validator = RegexValidator(
    regex=r"^\+?[0-9]{7,15}$",
    message="Enter a valid phone number using 7-15 digits and an optional leading +.",
)


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.PROTECT,
        related_name="students",
    )
    program = models.ForeignKey(
        "colleges.AcademicProgram",
        on_delete=models.PROTECT,
        related_name="students",
    )
    enrollment_number = models.CharField(
        max_length=40,
        validators=(enrollment_number_validator,),
    )
    graduation_year = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(2000), MaxValueValidator(2100)),
    )
    phone = models.CharField(max_length=16, blank=True, validators=(phone_validator,))
    profile_picture = models.ImageField(
        upload_to="students/profile-pictures/",
        blank=True,
        null=True,
    )
    date_of_birth = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=150, blank=True)
    career_objective = models.TextField(blank=True, max_length=1000)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    preferred_job_role = models.CharField(max_length=120, blank=True)
    preferred_locations = models.CharField(max_length=250, blank=True)
    is_visible_to_recruiters = models.BooleanField(
        default=True,
        help_text="Allow verified recruiters connected to this college to discover this profile.",
    )
    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        validators=(MinValueValidator(0), MaxValueValidator(10)),
    )
    tenth_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=(MinValueValidator(0), MaxValueValidator(100)),
    )
    twelfth_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=(MinValueValidator(0), MaxValueValidator(100)),
    )
    active_backlogs = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("user__first_name", "user__last_name", "enrollment_number")
        constraints = [
            models.UniqueConstraint(
                fields=("college", "enrollment_number"),
                name="unique_enrollment_number_per_college",
            )
        ]

    def clean(self):
        self.enrollment_number = self.enrollment_number.strip().upper()
        errors = {}
        if self.user_id and self.user.role != "STUDENT":
            errors["user"] = "The selected user must have the STUDENT role."
        if self.program_id and self.college_id and self.program.college_id != self.college_id:
            errors["program"] = "The selected program does not belong to this college."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.enrollment_number = self.enrollment_number.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.enrollment_number}"


class StudentImportBatch(models.Model):
    class Status(models.TextChoices):
        PREVIEW = "PREVIEW", "Ready to import"
        COMPLETED = "COMPLETED", "Completed"

    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.CASCADE,
        related_name="student_import_batches",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="student_import_batches",
    )
    original_filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PREVIEW)
    total_rows = models.PositiveSmallIntegerField(default=0)
    valid_rows = models.PositiveSmallIntegerField(default=0)
    invalid_rows = models.PositiveSmallIntegerField(default=0)
    imported_count = models.PositiveSmallIntegerField(default=0)
    rows = models.JSONField(default=list)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.college.code} - {self.original_filename} ({self.status})"


class Skill(models.Model):
    name = models.CharField(max_length=80, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class StudentSkill(models.Model):
    class Proficiency(models.TextChoices):
        BEGINNER = "BEGINNER", "Beginner"
        INTERMEDIATE = "INTERMEDIATE", "Intermediate"
        ADVANCED = "ADVANCED", "Advanced"
        EXPERT = "EXPERT", "Expert"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="skills",
    )
    skill = models.ForeignKey(Skill, on_delete=models.PROTECT, related_name="students")
    proficiency = models.CharField(
        max_length=20,
        choices=Proficiency.choices,
        default=Proficiency.BEGINNER,
    )
    years_experience = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0,
        validators=(MinValueValidator(0), MaxValueValidator(50)),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("skill__name",)
        constraints = [
            models.UniqueConstraint(
                fields=("student", "skill"),
                name="unique_skill_per_student",
            )
        ]

    def __str__(self):
        return f"{self.student.user.email} - {self.skill.name}"


class StudentProject(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    title = models.CharField(max_length=150)
    description = models.TextField(max_length=2000)
    technologies = models.CharField(max_length=500, blank=True)
    github_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_ongoing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_ongoing", "-start_date", "title")

    def clean(self):
        if self.is_ongoing and self.end_date:
            raise ValidationError({"end_date": "An ongoing project cannot have an end date."})
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before the start date."})

    def __str__(self):
        return f"{self.student.user.email} - {self.title}"


class StudentCertification(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="certifications",
    )
    name = models.CharField(max_length=180)
    issuing_organization = models.CharField(max_length=180)
    credential_id = models.CharField(max_length=120, blank=True)
    credential_url = models.URLField(blank=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-issue_date", "name")

    def clean(self):
        if self.expiry_date and self.expiry_date < self.issue_date:
            raise ValidationError({"expiry_date": "Expiry date cannot be before the issue date."})

    def __str__(self):
        return f"{self.student.user.email} - {self.name}"


class StudentExperience(models.Model):
    class EmploymentType(models.TextChoices):
        INTERNSHIP = "INTERNSHIP", "Internship"
        FULL_TIME = "FULL_TIME", "Full-time"
        PART_TIME = "PART_TIME", "Part-time"
        FREELANCE = "FREELANCE", "Freelance"
        VOLUNTEER = "VOLUNTEER", "Volunteer"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="experiences",
    )
    organization = models.CharField(max_length=180)
    role = models.CharField(max_length=150)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    location = models.CharField(max_length=150, blank=True)
    description = models.TextField(max_length=2000, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_current", "-start_date", "organization")

    def clean(self):
        if self.is_current and self.end_date:
            raise ValidationError({"end_date": "A current experience cannot have an end date."})
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before the start date."})

    def __str__(self):
        return f"{self.student.user.email} - {self.role} at {self.organization}"


def student_resume_upload_path(instance, filename):
    return f"students/resumes/{instance.student.user_id}/{filename}"


class StudentResume(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="resumes",
    )
    title = models.CharField(max_length=120)
    file = models.FileField(upload_to=student_resume_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_primary", "-updated_at")
        constraints = [
            models.UniqueConstraint(
                fields=("student",),
                condition=Q(is_primary=True),
                name="one_primary_resume_per_student",
            )
        ]

    def save(self, *args, **kwargs):
        if self.file:
            self.original_filename = self.original_filename or Path(self.file.name).name
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        storage = self.file.storage
        file_name = self.file.name
        result = super().delete(*args, **kwargs)
        if file_name:
            storage.delete(file_name)
        return result

    def __str__(self):
        return f"{self.student.user.email} - {self.title}"
