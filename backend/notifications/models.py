from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Category(models.TextChoices):
        COMPANY = "COMPANY", "Company request"
        APPLICATION = "APPLICATION", "Application"
        INTERVIEW = "INTERVIEW", "Interview"
        PLACEMENT = "PLACEMENT", "Placement"
        ANNOUNCEMENT = "ANNOUNCEMENT", "Announcement"
        SYSTEM = "SYSTEM", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    title = models.CharField(max_length=180)
    message = models.CharField(max_length=500)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("recipient", "is_read", "-created_at")),
        ]

    def __str__(self):
        return f"{self.recipient.email} - {self.title}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preference",
    )
    email_enabled = models.BooleanField(default=True)
    email_company = models.BooleanField(default=True)
    email_applications = models.BooleanField(default=True)
    email_interviews = models.BooleanField(default=True)
    email_placements = models.BooleanField(default=True)
    email_announcements = models.BooleanField(default=True)
    email_system = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} notification preferences"
