"""Move essay statuses onto the five-status set.

  ''      -> todo      (blank was already "not started"; three quarters of the
                        existing essays are this)
  'maybe' -> idea      ("maybe I'll write this" is closest to Idea Stage. No
                        rows have it locally, but production may.)
  'wip'   -> wip       unchanged
  'done'  -> done      unchanged — the dashboard and applications page count
                        status='done', and renaming the key would zero those
                        counts without failing loudly.

Lossless: every old value has a home, and nothing collapses two states into one.
"""
from django.db import migrations

MAP = {'': 'todo', 'maybe': 'idea'}
MODELS = ['SupplementEssay', 'UCPersonalInsightQuestion', 'CommonAppEssay']


def forwards(apps, schema_editor):
    for name in MODELS:
        Model = apps.get_model('supplements', name)
        for old, new in MAP.items():
            n = Model.objects.filter(status=old).update(status=new)
            if n:
                print(f'  {name}: {old!r} -> {new!r} on {n} row(s)')
        # Anything unrecognised (hand-edited, or a status from a future branch)
        # would fail validation and render as a blank pill. Park it in To Do
        # rather than leave it in limbo.
        known = {'todo', 'idea', 'wip', 'drafted', 'done'}
        stray = Model.objects.exclude(status__in=known)
        n = stray.count()
        if n:
            print(f'  {name}: {n} row(s) with an unknown status -> todo: '
                  f'{sorted(set(stray.values_list("status", flat=True)))}')
            stray.update(status='todo')


def backwards(apps, schema_editor):
    """todo -> '' and idea -> 'maybe'; drafted has no old equivalent, so it
    becomes 'wip' (the nearest in-progress state)."""
    back = {'todo': '', 'idea': 'maybe', 'drafted': 'wip'}
    for name in MODELS:
        Model = apps.get_model('supplements', name)
        for new, old in back.items():
            Model.objects.filter(status=new).update(status=old)


class Migration(migrations.Migration):

    dependencies = [
        ('supplements', '0005_alter_commonappessay_status_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
