from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("opportunities", "0005_remove_opportunity_is_open_to_all"),
        ("placements", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PlacementDrive",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True, max_length=2500)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("venue", models.CharField(blank=True, max_length=250)),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("UPCOMING", "Upcoming"), ("ONGOING", "Ongoing"), ("COMPLETED", "Completed"), ("CANCELLED", "Cancelled")], default="DRAFT", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("college", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="placement_drives", to="colleges.college")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_placement_drives", to=settings.AUTH_USER_MODEL)),
                ("opportunities", models.ManyToManyField(blank=True, related_name="placement_drives", to="opportunities.opportunity")),
            ],
            options={"ordering": ("-start_date", "title")},
        ),
    ]
