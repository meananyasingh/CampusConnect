from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ("colleges", "0002_academicprogram_collegeadminprofile"),
        ("companies", "0002_alter_companycollegepartnership_status"),
        ("opportunities", "0005_remove_opportunity_is_open_to_all"),
        ("placements", "0002_placementdrive"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="Announcement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("body", models.TextField(max_length=4000)),
                ("announcement_type", models.CharField(choices=[("GENERAL", "General update"), ("DEADLINE", "Deadline"), ("PRE_PLACEMENT", "Pre-placement talk"), ("ASSESSMENT", "Assessment"), ("INTERVIEW", "Interview"), ("RESULT", "Result")], default="GENERAL", max_length=30)),
                ("priority", models.CharField(choices=[("NORMAL", "Normal"), ("IMPORTANT", "Important"), ("URGENT", "Urgent")], default="NORMAL", max_length=20)),
                ("target_graduation_years", models.JSONField(blank=True, default=list)),
                ("publish_at", models.DateTimeField()),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("is_pinned", models.BooleanField(default=False)),
                ("is_archived", models.BooleanField(default=False)),
                ("approval_status", models.CharField(choices=[("PENDING", "Awaiting college approval"), ("APPROVED", "Approved"), ("REJECTED", "Rejected")], default="PENDING", max_length=20)),
                ("review_note", models.CharField(blank=True, max_length=500)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("college", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="announcements", to="colleges.college")),
                ("company", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="announcements", to="companies.company")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_announcements", to=settings.AUTH_USER_MODEL)),
                ("related_drive", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="announcements", to="placements.placementdrive")),
                ("related_opportunity", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="announcements", to="opportunities.opportunity")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_announcements", to=settings.AUTH_USER_MODEL)),
                ("target_programs", models.ManyToManyField(blank=True, related_name="announcements", to="colleges.academicprogram")),
            ],
            options={"ordering": ("-is_pinned", "-publish_at", "-created_at")},
        ),
        migrations.CreateModel(
            name="AnnouncementRead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("read_at", models.DateTimeField(auto_now_add=True)),
                ("announcement", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="read_receipts", to="announcements.announcement")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="announcement_reads", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(model_name="announcementread", constraint=models.UniqueConstraint(fields=("announcement", "user"), name="unique_announcement_read_per_user")),
    ]
