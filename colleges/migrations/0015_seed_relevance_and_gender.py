"""Mark obviously-relevant colleges, and record which admit one gender.

proof_acceptances started as "people Jacob knows who got in" and became the
relevance sort. That leaves 27 colleges he curated onto his own list — Barnard,
Bowdoin, Smith, Johns Hopkins — sorting down with the community-college
district offices, because nobody he knows happens to have gone there. 0.1 says
"obviously worth showing" without claiming an acceptance.

The Seven Sisters get the same treatment: they are the exact schools Lili came
for, and five of the six surviving ones were at 0.

The women's/men's list is hand-entered — IPEDS supplies no gender field in our
CSV, and this is deliberately the well-known, long-stable set rather than a
guess at all ~30. Several have gone co-ed recently (Wells, Chatham, Carlow;
Mills merged into Northeastern), so anything uncertain is left as 'all' — a
women's college wrongly flagged is worse than one not yet flagged, since the
flag can sink it down someone's list.
"""
from django.db import migrations

# Radcliffe merged into Harvard in 1999 and is correctly not in the data.
SEVEN_SISTERS = [
    'Barnard College',
    'Bryn Mawr College',
    'Mount Holyoke College',
    'Smith College',
    'Vassar College',
    'Wellesley College',
]

# Women's colleges: undergraduate admission still women-only, and long enough
# established to be confident without a source to check against.
WOMENS = [
    'Agnes Scott College',
    'Barnard College',
    'Bryn Mawr College',
    'Cedar Crest College',
    'College of Saint Benedict',
    'Converse University',
    'Cottey College',
    'Hollins University',
    'Meredith College',
    'Moore College of Art and Design',
    'Mount Holyoke College',
    'Russell Sage College',
    "Saint Mary's College",
    'Salem College',
    'Scripps College',
    'Simmons University',
    'Smith College',
    'Spelman College',
    'St Catherine University',
    'Stephens College',
    'Sweet Briar College',
    'Trinity Washington University',
    'Ursuline College',
    'Wellesley College',
    'Wesleyan College',
]

# Men's colleges. Deep Springs went co-ed in 2018 and is deliberately absent.
MENS = [
    'Hampden-Sydney College',
    'Morehouse College',
    'Wabash College',
]


def forwards(apps, schema_editor):
    College = apps.get_model('colleges', 'College')
    UserCollege = apps.get_model('colleges', 'UserCollege')

    # Anything anyone has put on a list is worth showing, whether or not
    # someone got in.
    on_a_list = set(
        UserCollege.objects.filter(college__isnull=False)
        .values_list('college_id', flat=True)
    )
    promoted = College.objects.filter(pk__in=on_a_list, proof_acceptances=0)
    n_promoted = promoted.count()
    promoted.update(proof_acceptances=0.1)

    sisters = College.objects.filter(name__in=SEVEN_SISTERS, proof_acceptances=0)
    n_sisters = sisters.count()
    sisters.update(proof_acceptances=0.1)

    n_w = College.objects.filter(name__in=WOMENS).update(gender_admission='women')
    n_m = College.objects.filter(name__in=MENS).update(gender_admission='men')

    missing = sorted(
        set(WOMENS + MENS) - set(
            College.objects.filter(name__in=WOMENS + MENS).values_list('name', flat=True)
        )
    )
    print(f'  relevance: {n_promoted} on-a-list college(s) -> 0.1; '
          f'{n_sisters} more of the Seven Sisters -> 0.1')
    print(f'  gender: {n_w} women\'s, {n_m} men\'s')
    if missing:
        print(f'  not found under these names (unflagged): {missing}')


def backwards(apps, schema_editor):
    College = apps.get_model('colleges', 'College')
    College.objects.filter(proof_acceptances=0.1).update(proof_acceptances=0)
    College.objects.exclude(gender_admission='all').update(gender_admission='all')


class Migration(migrations.Migration):

    dependencies = [
        ('colleges', '0014_college_gender_admission_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
