from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("opportunities", "0005_remove_opportunity_is_open_to_all"),
        ("students", "0004_studentresume"),
    ]
    operations = [
        migrations.CreateModel(
            name="OpportunityBookmark",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("opportunity", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="bookmarks", to="opportunities.opportunity")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="opportunity_bookmarks", to="students.studentprofile")),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.AddConstraint(model_name="opportunitybookmark", constraint=models.UniqueConstraint(fields=("student", "opportunity"), name="unique_student_opportunity_bookmark")),
    ]
