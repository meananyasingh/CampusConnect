from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class TalentPool(models.Model):
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="talent_pools",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_talent_pools",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("company", "name"),
                name="unique_talent_pool_name_per_company",
            )
        ]

    def clean(self):
        if self.created_by_id:
            profile = getattr(self.created_by, "recruiter_profile", None)
            if self.created_by.role != "RECRUITER" or not profile:
                raise ValidationError({"created_by": "A recruiter must create the talent pool."})
            if self.company_id and profile.company_id != self.company_id:
                raise ValidationError({"company": "The recruiter does not belong to this company."})

    def save(self, *args, **kwargs):
        self.name = " ".join(self.name.split())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class TalentPoolMember(models.Model):
    pool = models.ForeignKey(TalentPool, on_delete=models.CASCADE, related_name="members")
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="talent_pool_memberships",
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="added_talent_pool_members",
    )
    private_notes = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("pool", "student"),
                name="unique_student_per_talent_pool",
            )
        ]

    def __str__(self):
        return f"{self.pool.name} - {self.student.user.email}"

