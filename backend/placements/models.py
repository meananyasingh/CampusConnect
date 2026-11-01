from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class PlacementDrive(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        UPCOMING = "UPCOMING", "Upcoming"
        ONGOING = "ONGOING", "Ongoing"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.CASCADE,
        related_name="placement_drives",
    )
    title = models.CharField(max_length=180)
    description = models.TextField(max_length=2500, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    venue = models.CharField(max_length=250, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    opportunities = models.ManyToManyField(
        "opportunities.Opportunity",
        related_name="placement_drives",
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_placement_drives",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-start_date", "title")

    def clean(self):
        errors = {}
        if self.end_date and self.start_date and self.end_date < self.start_date:
            errors["end_date"] = "End date cannot be before the start date."
        if self.created_by_id and self.created_by.role != "ADMIN":
            errors["created_by"] = "The drive creator must be a college administrator."
        if self.created_by_id and self.college_id:
            admin_profile = getattr(self.created_by, "college_admin_profile", None)
            if admin_profile is None or admin_profile.college_id != self.college_id:
                errors["college"] = "The drive must belong to the administrator's college."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.college.code} - {self.title}"


class PlacementRecord(models.Model):
    class Status(models.TextChoices):
        OFFERED = "OFFERED", "Offer issued"
        ACCEPTED = "ACCEPTED", "Offer accepted"
        DECLINED = "DECLINED", "Offer declined"
        JOINED = "JOINED", "Joined company"
        CANCELLED = "CANCELLED", "Offer cancelled"

    application = models.OneToOneField(
        "applications.Application",
        on_delete=models.PROTECT,
        related_name="placement_record",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.PROTECT,
        related_name="placement_records",
    )
    annual_package = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=(MinValueValidator(0),),
    )
    offer_date = models.DateField()
    joining_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OFFERED)
    student_message = models.TextField(max_length=1500, blank=True)
    admin_notes = models.TextField(max_length=1500, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="verified_placement_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-offer_date", "-created_at")

    def clean(self):
        errors = {}
        if self.application_id:
            if self.application.status != "SELECTED":
                errors["application"] = "Only a selected application can become a placement record."
            if self.college_id and self.application.student.college_id != self.college_id:
                errors["college"] = "The placement college must match the student's college."
        if self.verified_by_id and self.verified_by.role != "ADMIN":
            errors["verified_by"] = "The placement verifier must be a college administrator."
        if self.joining_date and self.offer_date and self.joining_date < self.offer_date:
            errors["joining_date"] = "Joining date cannot be before the offer date."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.application.student.user.email} - {self.application.opportunity.company.name}"


class CollegePlacementPolicy(models.Model):
    college = models.OneToOneField(
        "colleges.College",
        on_delete=models.CASCADE,
        related_name="placement_policy",
    )
    applications_enabled = models.BooleanField(default=True)
    require_verified_documents = models.BooleanField(default=False)
    minimum_profile_completion = models.PositiveSmallIntegerField(
        default=0,
        validators=(MinValueValidator(0), MaxValueValidator(100)),
    )
    minimum_cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        validators=(MinValueValidator(0), MaxValueValidator(10)),
    )
    max_active_backlogs = models.PositiveSmallIntegerField(blank=True, null=True)
    student_message = models.CharField(max_length=500, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="updated_placement_policies",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "college placement policies"

    def clean(self):
        if self.updated_by_id:
            admin_profile = getattr(self.updated_by, "college_admin_profile", None)
            if self.updated_by.role != "ADMIN" or (
                admin_profile and admin_profile.college_id != self.college_id
            ):
                raise ValidationError({"updated_by": "The policy editor must administer this college."})

    def __str__(self):
        return f"{self.college.code} placement policy"
