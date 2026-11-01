from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Announcement(models.Model):
    class Type(models.TextChoices):
        GENERAL = "GENERAL", "General update"
        DEADLINE = "DEADLINE", "Deadline"
        PRE_PLACEMENT = "PRE_PLACEMENT", "Pre-placement talk"
        ASSESSMENT = "ASSESSMENT", "Assessment"
        INTERVIEW = "INTERVIEW", "Interview"
        RESULT = "RESULT", "Result"

    class Priority(models.TextChoices):
        NORMAL = "NORMAL", "Normal"
        IMPORTANT = "IMPORTANT", "Important"
        URGENT = "URGENT", "Urgent"

    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Awaiting college approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    college = models.ForeignKey("colleges.College", on_delete=models.CASCADE, related_name="announcements")
    company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="announcements", blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_announcements")
    title = models.CharField(max_length=180)
    body = models.TextField(max_length=4000)
    announcement_type = models.CharField(max_length=30, choices=Type.choices, default=Type.GENERAL)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    target_programs = models.ManyToManyField("colleges.AcademicProgram", related_name="announcements", blank=True)
    target_graduation_years = models.JSONField(default=list, blank=True)
    related_opportunity = models.ForeignKey("opportunities.Opportunity", on_delete=models.SET_NULL, related_name="announcements", blank=True, null=True)
    related_drive = models.ForeignKey("placements.PlacementDrive", on_delete=models.SET_NULL, related_name="announcements", blank=True, null=True)
    publish_at = models.DateTimeField()
    expires_at = models.DateTimeField(blank=True, null=True)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    review_note = models.CharField(max_length=500, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="reviewed_announcements", blank=True, null=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-is_pinned", "-publish_at", "-created_at")

    def clean(self):
        if self.expires_at and self.publish_at and self.expires_at <= self.publish_at:
            raise ValidationError({"expires_at": "Expiry must be after publication."})

    def __str__(self):
        return f"{self.college.code} - {self.title}"


class AnnouncementRead(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name="read_receipts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="announcement_reads")
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("announcement", "user"), name="unique_announcement_read_per_user")]

    def __str__(self):
        return f"{self.user.email} read {self.announcement_id}"
