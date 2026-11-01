from django.db import migrations


def mark_existing_targeted_opportunities(apps, schema_editor):
    Opportunity = apps.get_model("opportunities", "Opportunity")
    targeted_ids = Opportunity.target_colleges.through.objects.values_list(
        "opportunity_id",
        flat=True,
    ).distinct()
    Opportunity.objects.filter(id__in=targeted_ids).update(audience="COLLEGE")


class Migration(migrations.Migration):
    dependencies = [
        ("opportunities", "0002_opportunity_audience_and_more"),
    ]

    operations = [
        migrations.RunPython(mark_existing_targeted_opportunities, migrations.RunPython.noop),
    ]
