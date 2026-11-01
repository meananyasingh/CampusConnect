from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class College(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    logo = models.ImageField(upload_to="colleges/logos/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def save(self, *args, **kwargs):
        self.name = self.name.strip()
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AcademicProgram(models.Model):
    class Degree(models.TextChoices):
        BTECH = "BTECH", "Bachelor of Technology"
        BE = "BE", "Bachelor of Engineering"
        BCA = "BCA", "Bachelor of Computer Applications"
        BSC = "BSC", "Bachelor of Science"
        MCA = "MCA", "Master of Computer Applications"
        MSC = "MSC", "Master of Science"
        MBA = "MBA", "Master of Business Administration"
        OTHER = "OTHER", "Other"

    college = models.ForeignKey(
        College,
        on_delete=models.CASCADE,
        related_name="academic_programs",
    )
    degree = models.CharField(max_length=20, choices=Degree.choices)
    branch = models.CharField(max_length=150)
    duration_years = models.PositiveSmallIntegerField(default=4)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("degree", "branch")
        constraints = [
            models.UniqueConstraint(
                fields=("college", "degree", "branch"),
                name="unique_program_per_college",
            )
        ]

    def __str__(self):
        return f"{self.get_degree_display()} - {self.branch}"


class CollegeAdminProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="college_admin_profile",
    )
    college = models.ForeignKey(
        College,
        on_delete=models.PROTECT,
        related_name="administrators",
    )
    employee_id = models.CharField(max_length=50)
    designation = models.CharField(max_length=100, default="Placement Officer")
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("college", "employee_id")
        constraints = [
            models.UniqueConstraint(
                fields=("college", "employee_id"),
                name="unique_admin_employee_id_per_college",
            )
        ]

    def clean(self):
        if self.user_id and self.user.role != "ADMIN":
            raise ValidationError({"user": "The selected user must have the ADMIN role."})

    def save(self, *args, **kwargs):
        self.employee_id = self.employee_id.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.college.name}"
