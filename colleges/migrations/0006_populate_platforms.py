from django.db import migrations

# California State University schools
CSU_NAMES = {
    'Cal Poly Pomona',
    'San Diego State University',
    'San Jose State University',
    'Sonoma State University',
}

UCAS_NAMES = {
    'Oxford University',
    'Cambridge University',
    'Durham University',
}


def populate_platforms(apps, schema_editor):
    College = apps.get_model('colleges', 'College')
    for college in College.objects.all():
        name = college.name or ''
        if name.startswith('CSU ') or name in CSU_NAMES:
            college.app_platform = 'CSU'
        elif name in UCAS_NAMES:
            college.app_platform = 'UCAS'
        elif not college.app_platform:
            college.app_platform = 'Common'
        college.save()


class Migration(migrations.Migration):
    dependencies = [
        ('colleges', '0005_seed_hedgie_colleges'),
    ]

    operations = [
        migrations.RunPython(populate_platforms, migrations.RunPython.noop),
    ]
