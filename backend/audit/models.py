from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    class Category(models.TextChoices):
        ACCOUNT = "ACCOUNT", "Accounts"
        COMPANY = "COMPANY", "Companies"
        OPPORTUNITY = "OPPORTUNITY", "Opportunities"
        APPLICATION = "APPLICATION", "Applications"
        INTERVIEW = "INTERVIEW", "Interviews"
        DOCUMENT = "DOCUMENT", "Documents"
        PLACEMENT = "PLACEMENT", "Placements"
        COMMUNICATION = "COMMUNICATION", "Communications"
        SYSTEM = "SYSTEM", "System"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_events",
        blank=True,
        null=True,
    )
    actor_email = models.EmailField()
    actor_name = models.CharField(max_length=301, blank=True)
    actor_role = models.CharField(max_length=20)
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.SET_NULL,
        related_name="audit_events",
        blank=True,
        null=True,
    )
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.SET_NULL,
        related_name="audit_events",
        blank=True,
        null=True,
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    action = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    endpoint = models.CharField(max_length=255)
    http_method = models.CharField(max_length=10)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=80, blank=True)
    target_label = models.CharField(max_length=255, blank=True)
    changed_fields = models.JSONField(default=list)
    context = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("college", "-created_at")),
            models.Index(fields=("category", "-created_at")),
        ]

    def __str__(self):
        return f"{self.actor_email} - {self.action}"
