from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Opportunity(models.Model):
    class Type(models.TextChoices):
        JOB = "JOB", "Job"
        INTERNSHIP = "INTERNSHIP", "Internship"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    class WorkMode(models.TextChoices):
        ONSITE = "ONSITE", "On-site"
        REMOTE = "REMOTE", "Remote"
        HYBRID = "HYBRID", "Hybrid"

    class CompensationPeriod(models.TextChoices):
        YEAR = "YEAR", "Per year"
        MONTH = "MONTH", "Per month"

    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="opportunities",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_opportunities",
    )
    title = models.CharField(max_length=180)
    opportunity_type = models.CharField(max_length=20, choices=Type.choices)
    description = models.TextField(max_length=5000)
    responsibilities = models.TextField(max_length=3000, blank=True)
    qualifications = models.TextField(max_length=3000, blank=True)
    location = models.CharField(max_length=180)
    work_mode = models.CharField(max_length=20, choices=WorkMode.choices)
    openings = models.PositiveIntegerField(default=1, validators=(MinValueValidator(1),))
    compensation_min = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    compensation_max = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    compensation_period = models.CharField(
        max_length=10,
        choices=CompensationPeriod.choices,
        default=CompensationPeriod.YEAR,
    )
    application_deadline = models.DateField()
    min_cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        validators=(MinValueValidator(0), MaxValueValidator(10)),
    )
    max_active_backlogs = models.PositiveSmallIntegerField(default=0)
    graduation_year_from = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=(MinValueValidator(2000), MaxValueValidator(2100)),
    )
    graduation_year_to = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=(MinValueValidator(2000), MaxValueValidator(2100)),
    )
    target_colleges = models.ManyToManyField(
        "colleges.College",
        related_name="opportunities",
        blank=True,
    )
    eligible_programs = models.ManyToManyField(
        "colleges.AcademicProgram",
        related_name="opportunities",
        blank=True,
    )
    required_skills = models.ManyToManyField("students.Skill", related_name="opportunities", blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        errors = {}
        if self.created_by_id and self.created_by.role != "RECRUITER":
            errors["created_by"] = "The creator must have the RECRUITER role."
        if self.compensation_min is not None and self.compensation_max is not None:
            if self.compensation_max < self.compensation_min:
                errors["compensation_max"] = "Maximum compensation cannot be below the minimum."
        if self.graduation_year_from and self.graduation_year_to:
            if self.graduation_year_to < self.graduation_year_from:
                errors["graduation_year_to"] = "Ending graduation year cannot be before the starting year."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.company.name} - {self.title}"


class OpportunityBookmark(models.Model):
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="opportunity_bookmarks",
    )
    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name="bookmarks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("student", "opportunity"),
                name="unique_student_opportunity_bookmark",
            )
        ]

    def __str__(self):
        return f"{self.student.user.email} saved {self.opportunity.title}"


class OpportunityCollegeInvitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Awaiting college review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn by recruiter"

    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name="college_invitations",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.CASCADE,
        related_name="opportunity_invitations",
    )
    eligible_programs = models.ManyToManyField(
        "colleges.AcademicProgram",
        related_name="opportunity_invitations",
        blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    recruiter_message = models.TextField(max_length=1000, blank=True)
    review_note = models.TextField(max_length=1000, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_opportunity_invitations",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_opportunity_invitations",
        blank=True,
        null=True,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-submitted_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("opportunity", "college"),
                name="unique_opportunity_invitation_per_college",
            )
        ]

    def clean(self):
        errors = {}
        if self.submitted_by_id and self.submitted_by.role != "RECRUITER":
            errors["submitted_by"] = "The invitation must be submitted by a recruiter."
        if self.pk and self.college_id and self.eligible_programs.exclude(
            college_id=self.college_id
        ).exists():
            errors["eligible_programs"] = "Eligible programs must belong to the invited college."
        if self.reviewed_by_id:
            admin_profile = getattr(self.reviewed_by, "college_admin_profile", None)
            if self.reviewed_by.role != "ADMIN" or (
                admin_profile and admin_profile.college_id != self.college_id
            ):
                errors["reviewed_by"] = "The reviewer must administer the invited college."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.opportunity.title} - {self.college.code} ({self.get_status_display()})"
