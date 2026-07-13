"""
Backfill latitude/longitude (and city/state) onto existing canonical College
records by matching their names against colleges_ipeds.csv.

Scoped to the ~100 colleges already in the DB (NOT a full IPEDS import — that's
the larger source-of-truth migration). Dry-run by default; pass --commit to save.

    python manage.py backfill_coordinates              # dry run, prints report
    python manage.py backfill_coordinates --commit      # save AUTO matches
    python manage.py backfill_coordinates --commit --include-review

Matching: a candidate must contain ALL of the college's core tokens (coverage
== 1.0). Among full-coverage candidates we prefer, in order: exact token-set
match, higher proof_acceptances (a flagship-campus popularity proxy), then the
tightest token overlap. This resolves multi-campus traps (U Washington ->
Seattle, U Maryland -> College Park, Georgia Tech -> Main Campus).

Tiers:
    AUTO    coverage == 1.0            — saved on --commit
    REVIEW  0.5 <= coverage < 1.0      — printed only; saved with --include-review
    NONE    coverage < 0.5             — left untouched (e.g. international schools)
"""
import csv
import os
import re

from django.conf import settings
from django.core.management.base import BaseCommand

from colleges.models import College

# Whole-name alias expansions, keyed on the NORMALIZED name (lowercased,
# parentheticals stripped). Only for abbreviations token matching can't bridge.
ALIASES = {
    'uc berkeley': 'university of california berkeley',
    'ucla': 'university of california los angeles',
    'uc davis': 'university of california davis',
    'uc irvine': 'university of california irvine',
    'uc merced': 'university of california merced',
    'uc riverside': 'university of california riverside',
    'uc san diego': 'university of california san diego',
    'uc santa barbara': 'university of california santa barbara',
    'uc santa cruz': 'university of california santa cruz',
    'csu east bay': 'california state university east bay',
    'csu fullerton': 'california state university fullerton',
    'csu humboldt': 'california state polytechnic university humboldt',
    'csu long beach': 'california state university long beach',
    'csu monterey': 'california state university monterey bay',
    'cal poly pomona': 'california state polytechnic university pomona',
    'usc': 'university of southern california',
    'usf': 'university of san francisco',
    'umass amherst': 'university of massachusetts amherst',
    'wash u': 'washington university st louis',
    'georgia tech': 'georgia institute technology',
    'virginia tech': 'virginia polytechnic institute state university',
    'caltech': 'california institute technology',
    'unc chapel hill': 'university north carolina chapel hill',
    'u colorado boulder': 'university colorado boulder',
    'nyu': 'new york university',
    'scad': 'savannah college art design',
    'rose hulman university': 'rose hulman institute technology',
}

# Manual overrides keyed by EXACT College.name, for cases the token+popularity
# heuristic gets wrong. Value = exact IPEDS name, or None for "no IPEDS match"
# (e.g. international schools not in the US dataset).
OVERRIDES = {
    'Amherst': 'Amherst College',                       # else -> UMass-Amherst (higher popularity)
    'University of Miami, Florida': 'University of Miami',  # 'Florida' token pulls it to U of Florida
    # No US IPEDS match — international or absent from the dataset. Force no-match
    # so they don't get bogus coordinates from a low-confidence token overlap.
    'Oxford University': None,        # UK
    'Cambridge University': None,     # UK
    'University of Warwick': None,    # UK
    'Durham University': None,        # UK
    'University of Toronto': None,    # Canada
    'University of Waterloo': None,   # Canada
    'McGill': None,                   # Canada
    'TU Delft': None,                 # Netherlands
    'Deep Springs': None,            # not in IPEDS
    'Grand Canyon University': None,  # not in IPEDS
}

TOKEN_EXPAND = {'univ': 'university', 'u': 'university', 'inst': 'institute', 'st': 'saint'}
STOP = {'of', 'the', 'at', 'in', 'and', 'a', '&', ''}


def normalize(s):
    s = s.lower()
    s = re.sub(r'\(.*?\)', ' ', s)          # drop parentheticals e.g. (UCSB)
    s = s.replace('&', ' and ')
    s = re.sub(r'[.,\-/]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    s = ALIASES.get(s, s)
    tokens = [TOKEN_EXPAND.get(t, t) for t in s.split()]
    return ' '.join(tokens)


def core_tokens(s):
    return {t for t in normalize(s).split() if t not in STOP}


class Command(BaseCommand):
    help = 'Backfill lat/long/city/state on existing colleges from colleges_ipeds.csv'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', help='Save matches (default: dry run)')
        parser.add_argument('--include-review', action='store_true',
                            help='Also save REVIEW-tier (0.5-1.0 coverage) matches')
        parser.add_argument('--csv', type=str, default=None, help='Path to IPEDS CSV')

    def handle(self, *args, **opts):
        csv_path = opts['csv'] or os.path.join(settings.BASE_DIR, 'colleges_ipeds.csv')
        if not os.path.exists(csv_path):
            self.stderr.write(f'CSV not found: {csv_path}')
            return

        index = []  # (token_set, proof_int, row)
        by_name = {}
        with open(csv_path, newline='', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                by_name[row['name']] = row
                if not (row.get('latitude') and row.get('longitude')):
                    continue
                try:
                    proof = int(row.get('proof_acceptances') or 0)
                except ValueError:
                    proof = 0
                index.append((core_tokens(row['name']), proof, row))

        auto = review = none = skipped = 0
        report = []

        for c in College.objects.all():
            if c.latitude is not None and c.longitude is not None:
                skipped += 1
                continue
            if c.name in OVERRIDES:
                target = OVERRIDES[c.name]
                if target is None:
                    report.append(('NONE', 0.0, c.name, '— (override: no IPEDS match)', '', '', '', ''))
                    none += 1
                    continue
                best, best_cov, tier = by_name.get(target), 1.0, 'AUTO'
                if best is None:
                    self.stderr.write(f'OVERRIDE target not found in CSV: {target!r}')
                    continue
            else:
                ct = core_tokens(c.name)
                if not ct:
                    report.append(('NONE', 0.0, c.name, '—', '', '', '', ''))
                    none += 1
                    continue

                best, best_key, best_cov = None, None, 0.0
                for it, proof, row in index:
                    inter = ct & it
                    cov = len(inter) / len(ct)
                    exact = 1 if ct == it else 0
                    jac = len(inter) / len(ct | it)
                    key = (cov, exact, proof, jac)
                    if best_key is None or key > best_key:
                        best, best_key, best_cov = row, key, cov

                if best_cov >= 1.0:
                    tier = 'AUTO'
                elif best_cov >= 0.5:
                    tier = 'REVIEW'
                else:
                    tier = 'NONE'

            report.append((tier, best_cov, c.name,
                           best['name'] if best else '—',
                           best['city'] if best else '', best['state'] if best else '',
                           best['latitude'] if best else '', best['longitude'] if best else ''))

            if opts['commit'] and (tier == 'AUTO' or (tier == 'REVIEW' and opts['include_review'])):
                c.latitude = float(best['latitude'])
                c.longitude = float(best['longitude'])
                if best.get('city'):
                    c.city = best['city']
                if best.get('state'):
                    c.state = best['state']
                c.save(update_fields=['latitude', 'longitude', 'city', 'state'])

            auto += tier == 'AUTO'
            review += tier == 'REVIEW'
            none += tier == 'NONE'

        order = {'AUTO': 0, 'REVIEW': 1, 'NONE': 2}
        for tier, cov, name, match, city, state, lat, lon in sorted(
                report, key=lambda r: (order[r[0]], -r[1], r[2].lower())):
            self.stdout.write(f'{tier:6} cov={cov:.2f}  {name:38.38} -> {match:44.44} {city},{state}')

        self.stdout.write('')
        self.stdout.write(f'AUTO={auto}  REVIEW={review}  NONE={none}  already-had-coords={skipped}')
        if not opts['commit']:
            self.stdout.write(self.style.WARNING('DRY RUN — nothing saved. Re-run with --commit to save AUTO matches.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Committed {auto + (review if opts["include_review"] else 0)} matches.'))
