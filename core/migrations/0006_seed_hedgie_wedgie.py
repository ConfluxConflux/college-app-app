from django.db import migrations


def seed_hedgie_wedgie(apps, schema_editor):
    Applicant = apps.get_model('core', 'Applicant')
    Applicant.objects.create(
        first_name='Hedgie',
        last_name='Wedgie',
        email='hedgiewedgie@proofschool.org',
        profile_picture='img/default_profile.png',
    )


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_coreactivity_grade_10_coreactivity_grade_11_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_hedgie_wedgie, migrations.RunPython.noop),
    ]
