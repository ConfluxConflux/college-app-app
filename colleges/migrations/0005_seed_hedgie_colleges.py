from django.db import migrations


USER_SPECIFIC_FIELDS = [
    'apply_status', 'collegevine_chance', 'intended_major', 'second_choice_major',
    'third_choice_major', 'self_report_sat', 'interview', 'known_students',
    'known_faculty', 'toured', 'portal_info', 'applicant_notes', 'parent_notes',
    'random_notes',
]


def seed_hedgie_colleges(apps, schema_editor):
    Applicant = apps.get_model('core', 'Applicant')
    College = apps.get_model('colleges', 'College')

    try:
        jacob = Applicant.objects.get(pk=1)
        hedgie = Applicant.objects.get(pk=2)
    except Applicant.DoesNotExist:
        return

    for c in College.objects.filter(applicant=jacob).order_by('order'):
        new = College(applicant=hedgie)
        # Copy all fields from Jacob's college
        for field in College._meta.fields:
            if field.name not in ('id', 'applicant') and not field.name in USER_SPECIFIC_FIELDS:
                setattr(new, field.name, getattr(c, field.name))
        # Reset user-specific fields
        new.apply_status = 'not_applying'
        new.collegevine_chance = ''
        new.intended_major = ''
        new.second_choice_major = ''
        new.third_choice_major = ''
        new.self_report_sat = ''
        new.interview = ''
        new.known_students = ''
        new.known_faculty = ''
        new.toured = ''
        new.portal_info = ''
        new.applicant_notes = ''
        new.parent_notes = ''
        new.random_notes = ''
        new.save()


class Migration(migrations.Migration):
    dependencies = [
        ('colleges', '0004_college_apply_status_default'),
        ('core', '0006_seed_hedgie_wedgie'),
    ]

    operations = [
        migrations.RunPython(seed_hedgie_colleges, migrations.RunPython.noop),
    ]
