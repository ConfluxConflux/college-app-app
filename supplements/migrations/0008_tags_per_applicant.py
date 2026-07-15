"""Give every applicant their own copy of the essay tags.

Tags were global, so renaming one renamed it for everyone — which defeats the
point, since a tag's job is to reflect how one person groups their essays.

Each applicant gets a clone of the existing set, every essay is repointed to
its own applicant's clone by name, and the old ownerless rows are dropped.
Matching by name is safe here: the clones are made from those exact rows.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    EssayCategory = apps.get_model('supplements', 'EssayCategory')
    SupplementEssay = apps.get_model('supplements', 'SupplementEssay')
    Applicant = apps.get_model('core', 'Applicant')

    originals = list(EssayCategory.objects.filter(applicant__isnull=True).order_by('sort_order', 'name'))
    if not originals:
        return

    # name -> {applicant_id: new tag}
    clones = {}
    for applicant in Applicant.objects.all():
        for orig in originals:
            clone = EssayCategory.objects.create(
                applicant=applicant, name=orig.name, sort_order=orig.sort_order
            )
            clones.setdefault(orig.name, {})[applicant.id] = clone

    by_id = {o.id: o.name for o in originals}
    repointed = orphaned = 0
    for essay in SupplementEssay.objects.filter(category__isnull=False):
        name = by_id.get(essay.category_id)
        if name is None:
            continue  # already per-applicant somehow; leave it
        target = clones.get(name, {}).get(essay.applicant_id)
        if target is None:
            # An essay with no applicant can't be given an owned tag. Its
            # applicant is backfilled by 0004, so this should not happen —
            # drop the tag rather than point at someone else's.
            essay.category = None
            orphaned += 1
        else:
            essay.category_id = target.id
            repointed += 1
        essay.save(update_fields=['category'])

    n = len(originals)
    EssayCategory.objects.filter(applicant__isnull=True).delete()
    print(f'  cloned {n} tags for {Applicant.objects.count()} applicant(s); '
          f'repointed {repointed} essay(s)'
          + (f'; {orphaned} left untagged' if orphaned else ''))


def backwards(apps, schema_editor):
    """Collapse back to one global set, keeping the first copy of each name."""
    EssayCategory = apps.get_model('supplements', 'EssayCategory')
    SupplementEssay = apps.get_model('supplements', 'SupplementEssay')

    seen = {}
    for tag in EssayCategory.objects.filter(applicant__isnull=False).order_by('sort_order', 'name', 'id'):
        if tag.name not in seen:
            tag.applicant = None
            tag.save(update_fields=['applicant'])
            seen[tag.name] = tag
        else:
            SupplementEssay.objects.filter(category=tag).update(category=seen[tag.name])
            tag.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('supplements', '0007_essaycategory_applicant_and_more'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
