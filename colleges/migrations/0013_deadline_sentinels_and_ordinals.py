"""Clear the en-dash deadline sentinels and backfill deadline_ordinal.

Jacob's spreadsheet used a literal en-dash to mean "this college doesn't offer
this round". As data that is a lie: it renders as a dash rather than nothing,
and it would sort as if it were a date. Blank means the same thing honestly.

Also seeds deadline_ordinal for every existing row. The property that computes
it doesn't exist on historical models, so the resolution order (override ->
round -> RD) is repeated here deliberately.
"""
from django.db import migrations

from colleges.models import cycle_ordinal, parse_month_day

DEADLINE_FIELDS = [
    'ea_deadline_override',
    'ed1_deadline_override',
    'ed2_deadline_override',
    'rd_deadline_override',
    'other_deadline_override',
    'financial_aid_deadline_override',
]

SENTINELS = {'-', '–', '—'}

ROUND_FIELD = {'ea': 'ea_deadline', 'ed1': 'ed1_deadline', 'ed2': 'ed2_deadline', 'rd': 'rd_deadline'}


def _effective(uc, college, field):
    v = getattr(uc, field + '_override', '')
    if v:
        return v
    return getattr(college, field, '') if college else ''


def forwards(apps, schema_editor):
    UserCollege = apps.get_model('colleges', 'UserCollege')

    cleared = 0
    for uc in UserCollege.objects.all():
        dirty = []
        for f in DEADLINE_FIELDS:
            if (getattr(uc, f) or '').strip() in SENTINELS:
                setattr(uc, f, '')
                dirty.append(f)
                cleared += 1
        if dirty:
            uc.save(update_fields=dirty)

    filled = 0
    for uc in UserCollege.objects.select_related('college').all():
        college = uc.college
        if uc.deadline_override:
            text = uc.deadline_override
        elif uc.application_round == 'rolling':
            text = ''
        elif uc.application_round in ROUND_FIELD:
            text = _effective(uc, college, ROUND_FIELD[uc.application_round])
        else:
            text = _effective(uc, college, 'rd_deadline')

        md = parse_month_day(text)
        ordinal = cycle_ordinal(*md) if md else None
        if uc.deadline_ordinal != ordinal:
            uc.deadline_ordinal = ordinal
            uc.save(update_fields=['deadline_ordinal'])
            if ordinal is not None:
                filled += 1

    print(f'  cleared {cleared} en-dash sentinels; seeded {filled} deadline ordinals')


def backwards(apps, schema_editor):
    """The sentinels are not restored: '' already means what they meant."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0012_usercollege_application_round_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
