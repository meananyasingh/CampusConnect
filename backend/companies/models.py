from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Company(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, editable=False)
    industry = models.CharField(max_length=120)
    website = models.URLField()
    contact_email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    headquarters = models.CharField(max_length=180, blank=True)
    company_size = models.CharField(max_length=80, blank=True)
    description = models.TextField(max_length=2500, blank=True)
    linkedin_url = models.URLField(blank=True)
    logo = models.ImageField(upload_to="companies/logos/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)
        verbose_name_plural = "companies"

    def save(self, *args, **kwargs):
        self.name = " ".join(self.name.split())
        if not self.slug:
            base_slug = slugify(self.name)[:200] or "company"
            candidate = base_slug
            counter = 2
            while Company.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecruiterProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recruiter_profile",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="recruiters",
    )
    designation = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)
    is_company_owner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("company", "user__first_name", "user__last_name")

    def clean(self):
        if self.user_id and self.user.role != "RECRUITER":
            raise ValidationError({"user": "The selected user must have the RECRUITER role."})

    def __str__(self):
        return f"{self.user.email} - {self.company.name}"


class CompanyCollegePartnership(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Awaiting college response"
        VERIFIED = "VERIFIED", "Approved to recruit"
        REJECTED = "REJECTED", "Request declined"
        SUSPENDED = "SUSPENDED", "Recruitment paused"

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="college_partnerships",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.CASCADE,
        related_name="company_partnerships",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    review_note = models.CharField(max_length=500, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="reviewed_company_partnerships",
        blank=True,
        null=True,
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("company", "college"),
                name="unique_company_college_partnership",
            )
        ]

    def clean(self):
        if self.reviewed_by_id and self.reviewed_by.role != "ADMIN":
            raise ValidationError({"reviewed_by": "The reviewer must have the ADMIN role."})

    def __str__(self):
        return f"{self.company.name} - {self.college.name} ({self.get_status_display()})"
