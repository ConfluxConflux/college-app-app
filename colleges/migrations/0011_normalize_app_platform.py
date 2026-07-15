"""Normalize app_platform_override to the lowercase APP_PLATFORM_CHOICES keys.

Values were stored Title-Case ('Common') while the choices use lowercase keys
('common'). applications() compares exactly, so the platform label and the
activities panel rendered blank for every row. This makes that code live.

Casing only — no judgement about which platform a college actually uses.
Canonical College.app_platform stays empty until a real Common App member list
is imported; the per-user override remains the only platform data there is.
"""
from django.db import migrations


# 'UC + CCS' is UC Santa Barbara's College of Creative Studies — still the UC
# application. 'minerva' is a real choice: the platform tracker has a row for it.
MAP = {
    'common': 'common',
    'csu': 'csu',
    'uc': 'uc',
    'ucas': 'ucas',
    'canada': 'canada',
    'mit': 'mit',
    'georgetown': 'georgetown',
    'coalition': 'coalition',
    'minerva': 'minerva',
    'uc + ccs': 'uc',
}


def normalize(apps, schema_editor):
    UserCollege = apps.get_model('colleges', 'UserCollege')
    College = apps.get_model('colleges', 'College')
    for model, field in ((UserCollege, 'app_platform_override'), (College, 'app_platform')):
        for obj in model.objects.exclude(**{field: ''}):
            raw = (getattr(obj, field) or '').strip()
            new = MAP.get(raw.lower())
            if new is None:
                new = 'other' if raw else ''
            if new != raw:
                setattr(obj, field, new)
                obj.save(update_fields=[field])


def denormalize(apps, schema_editor):
    """Best-effort reverse: restore the Title-Case forms that were there before."""
    BACK = {'common': 'Common', 'csu': 'CSU', 'uc': 'UC', 'ucas': 'UCAS',
            'canada': 'Canada', 'mit': 'MIT', 'georgetown': 'Georgetown'}
    UserCollege = apps.get_model('colleges', 'UserCollege')
    for uc in UserCollege.objects.exclude(app_platform_override=''):
        old = BACK.get(uc.app_platform_override)
        if old:
            uc.app_platform_override = old
            uc.save(update_fields=['app_platform_override'])


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0010_backfill_apply_status_not_applying'),
    ]

    operations = [
        migrations.RunPython(normalize, denormalize),
    ]
