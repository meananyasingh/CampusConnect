from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "APPLIED", "Applied"
        UNDER_REVIEW = "UNDER_REVIEW", "Under review"
        SHORTLISTED = "SHORTLISTED", "Shortlisted"
        INTERVIEW = "INTERVIEW", "Interview stage"
        SELECTED = "SELECTED", "Selected"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    opportunity = models.ForeignKey(
        "opportunities.Opportunity",
        on_delete=models.PROTECT,
        related_name="applications",
    )
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="applications",
    )
    resume = models.ForeignKey(
        "students.StudentResume",
        on_delete=models.PROTECT,
        related_name="applications",
    )
    cover_letter = models.TextField(max_length=3000, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-applied_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("opportunity", "student"),
                name="unique_student_application_per_opportunity",
            )
        ]

    def clean(self):
        if self.resume_id and self.student_id and self.resume.student_id != self.student_id:
            raise ValidationError({"resume": "The resume must belong to the applicant."})

    def __str__(self):
        return f"{self.student.user.email} - {self.opportunity.title}"


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    from_status = models.CharField(max_length=20, choices=Application.Status.choices, blank=True)
    to_status = models.CharField(max_length=20, choices=Application.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="application_status_changes",
        blank=True,
        null=True,
    )
    note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name_plural = "application status histories"

    def __str__(self):
        return f"{self.application_id}: {self.from_status or 'New'} → {self.to_status}"


class RecruitmentRound(models.Model):
    class Type(models.TextChoices):
        SCREENING = "SCREENING", "Screening"
        APTITUDE = "APTITUDE", "Aptitude test"
        GROUP_DISCUSSION = "GROUP_DISCUSSION", "Group discussion"
        TECHNICAL = "TECHNICAL", "Technical interview"
        HR = "HR", "HR interview"
        OTHER = "OTHER", "Other"

    opportunity = models.ForeignKey(
        "opportunities.Opportunity",
        on_delete=models.CASCADE,
        related_name="recruitment_rounds",
    )
    name = models.CharField(max_length=150)
    round_type = models.CharField(max_length=30, choices=Type.choices)
    sequence = models.PositiveSmallIntegerField(validators=(MinValueValidator(1),))
    description = models.TextField(max_length=1500, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_recruitment_rounds",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("opportunity", "sequence")
        constraints = [
            models.UniqueConstraint(
                fields=("opportunity", "sequence"),
                name="unique_round_sequence_per_opportunity",
            )
        ]

    def clean(self):
        if self.created_by_id and self.created_by.role != "RECRUITER":
            raise ValidationError({"created_by": "The round creator must be a recruiter."})

    def __str__(self):
        return f"{self.opportunity.title} - Round {self.sequence}: {self.name}"


class InterviewSchedule(models.Model):
    class Mode(models.TextChoices):
        ONLINE = "ONLINE", "Online"
        ONSITE = "ONSITE", "On-site"
        PHONE = "PHONE", "Phone"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class Result(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PASSED = "PASSED", "Passed"
        FAILED = "FAILED", "Not selected for next round"
        NO_SHOW = "NO_SHOW", "Candidate did not attend"

    recruitment_round = models.ForeignKey(
        RecruitmentRound,
        on_delete=models.CASCADE,
        related_name="interviews",
    )
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="interviews",
    )
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(
        default=45,
        validators=(MinValueValidator(10), MaxValueValidator(480)),
    )
    mode = models.CharField(max_length=20, choices=Mode.choices)
    venue = models.CharField(max_length=250, blank=True)
    meeting_link = models.URLField(blank=True)
    instructions = models.TextField(max_length=1500, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    result = models.CharField(max_length=20, choices=Result.choices, default=Result.PENDING)
    feedback = models.TextField(max_length=2000, blank=True)
    rating = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=(MinValueValidator(1), MaxValueValidator(5)),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_interview_schedules",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("scheduled_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("recruitment_round", "application"),
                name="unique_candidate_per_recruitment_round",
            )
        ]

    def clean(self):
        errors = {}
        if (
            self.recruitment_round_id
            and self.application_id
            and self.recruitment_round.opportunity_id != self.application.opportunity_id
        ):
            errors["application"] = "The application and recruitment round must belong to the same opportunity."
        if self.created_by_id and self.created_by.role != "RECRUITER":
            errors["created_by"] = "The interview creator must be a recruiter."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.application.student.user.email} - {self.recruitment_round.name}"
