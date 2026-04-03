from django.db import migrations


def fix_hedgie_email(apps, schema_editor):
    Applicant = apps.get_model('core', 'Applicant')
    Applicant.objects.filter(first_name='Hedgie', last_name='Wedgie').update(
        email='hedgiewedgie@proofschool.org'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_update_site_domain'),
    ]

    operations = [
        migrations.RunPython(fix_hedgie_email, migrations.RunPython.noop),
    ]
