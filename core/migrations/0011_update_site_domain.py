from django.db import migrations


def update_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(id=1).update(domain='hippocampus.college', name='Hippocampus')


def revert_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(id=1).update(domain='collegeappapp.com', name='College App App')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_applicant_user'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(update_site, revert_site),
    ]
