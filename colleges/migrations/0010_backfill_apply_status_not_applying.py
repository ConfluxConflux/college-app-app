from django.db import migrations


def backfill_not_applying(apps, schema_editor):
    UserCollege = apps.get_model('colleges', 'UserCollege')
    UserCollege.objects.filter(apply_status='').update(apply_status='not_applying')


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0009_alter_usercollege_options_alter_college_id_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_not_applying, migrations.RunPython.noop),
    ]
