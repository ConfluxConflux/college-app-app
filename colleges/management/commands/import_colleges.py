"""Import canonical college data from colleges_ipeds.csv into College.

The CSV is IPEDS plus a handful of hand-added foreign schools, which have no
unitid. Identity is therefore unitid when present and name otherwise.

Existing College rows predate the canonical split and have no unitid, but carry
UserCollege foreign keys. They are matched by name and updated in place so the
pk (and every FK to it) survives. Matching never guesses: a row is only adopted
when the name resolves to exactly one CSV row. Anything else is reported for a
human, because binding an application record to the wrong school is worse than
leaving it unlinked.
"""
import csv
import os
import re

from django.core.management.base import BaseCommand
from django.db import transaction

from colleges.models import College

# Hand-verified shorthand. Each must resolve to exactly one CSV row; the
# importer aborts on any alias that does not, rather than silently skipping.
ALIASES = {
    'caltech': 'California Institute of Technology',
    'ucla': 'University of California-Los Angeles',
    'usc': 'University of Southern California',
    'usf': 'University of San Francisco',
    'scad': 'Savannah College of Art and Design',
    'wash u': 'Washington University in St Louis',
    'georgia tech': 'Georgia Institute of Technology-Main Campus',
    'virginia tech': 'Virginia Polytechnic Institute and State University',
    'texas a and m': 'Texas A & M University-College Station',
    'umass amherst': 'University of Massachusetts-Amherst',
    'unc chapel hill': 'University of North Carolina at Chapel Hill',
    'case western': 'Case Western Reserve University',
    'colorado state': 'Colorado State University-Fort Collins',
    'ohio state': 'Ohio State University-Main Campus',
    'cal poly pomona': 'California State Polytechnic University-Pomona',
    'uc berkeley': 'University of California-Berkeley',
    'uc davis': 'University of California-Davis',
    'uc irvine': 'University of California-Irvine',
    'uc merced': 'University of California-Merced',
    'uc riverside': 'University of California-Riverside',
    'uc san diego': 'University of California-San Diego',
    'uc santa barbara': 'University of California-Santa Barbara',
    'uc santa cruz': 'University of California-Santa Cruz',
    'csu east bay': 'California State University-East Bay',
    'csu fullerton': 'California State University-Fullerton',
    'csu humboldt': 'California State Polytechnic University-Humboldt',
    'csu long beach': 'California State University-Long Beach',
    'csu monterey': 'California State University-Monterey Bay',
    'univ of maryland': 'University of Maryland-College Park',
    'university of miami florida': 'University of Miami',
    'u colorado boulder': 'University of Colorado Boulder',
    'univ of minnesota twin cities': 'University of Minnesota-Twin Cities',
    'university of alabama huntsville': 'University of Alabama in Huntsville',
    'university of texas austin': 'The University of Texas at Austin',
    'rochester inst of technology': 'Rochester Institute of Technology',
}

SUFFIXES = (' college', ' university', ' institute of technology', ' institute')


def norm(s):
    s = s.lower().strip()
    s = re.sub(r'\([^)]*\)', ' ', s)        # "Boston University (BU)" -> "boston university"
    s = s.replace('&', ' and ')
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def strip_suffix(n):
    for suf in SUFFIXES:
        if n.endswith(suf):
            return n[: -len(suf)].strip()
    return n


def to_int(v):
    if v is None:
        return None
    v = str(v).replace(',', '').replace('$', '').strip()
    if not v:
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def to_float(v):
    if v is None:
        return None
    v = str(v).strip()
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


class Matcher:
    def __init__(self, rows):
        self.rows = rows
        self.by_exact, self.by_norm, self.by_stem = {}, {}, {}
        for r in rows:
            self.by_exact.setdefault(r['name'], []).append(r)
            self.by_norm.setdefault(r['_n'], []).append(r)
            self.by_stem.setdefault(r['_stem'], []).append(r)

    def match(self, name):
        """Return (row, method) on a confident match, else (None, candidates)."""
        n = norm(name)
        stem = strip_suffix(n)

        if len(self.by_exact.get(name, [])) == 1:
            return self.by_exact[name][0], 'exact'
        if len(self.by_norm.get(n, [])) == 1:
            return self.by_norm[n][0], 'normalized'
        if len(self.by_stem.get(stem, [])) == 1:
            return self.by_stem[stem][0], 'stem'
        if n in ALIASES:
            hits = self.by_exact.get(ALIASES[n], [])
            if len(hits) == 1:
                return hits[0], 'alias'
            return None, []

        # Prefix, then proof_acceptances as a tiebreak between campuses of the
        # same system. "arizona state university" prefixes "Arizona State
        # University Campus Immersion" but not "Winona State University" —
        # which is why this is a prefix test and not a similarity score.
        for key in ('_n', '_stem'):
            base = n if key == '_n' else stem
            pre = [r for r in self.rows if r[key] == base or r[key].startswith(base + ' ')]
            if len(pre) == 1:
                return pre[0], 'prefix' if key == '_n' else 'stem-prefix'
            if len(pre) > 1:
                certified = [r for r in pre if r['_proof'] > 0]
                if len(certified) == 1:
                    return certified[0], ('prefix+proof' if key == '_n' else 'stem-prefix+proof')
                return None, pre
        return None, []


class Command(BaseCommand):
    help = 'Import canonical college data from colleges_ipeds.csv into College.'

    def add_arguments(self, parser):
        parser.add_argument('--csv', default='colleges_ipeds.csv')
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would happen; write nothing.')
        parser.add_argument('--matches', default='colleges_manual_matches.csv',
                            help='CSV of name,unitid resolving reported ambiguities. Keyed by '
                                 'name rather than pk so the same file works against any database.')
        parser.add_argument('--keep-display-names', action='store_true', default=True,
                            help='Preserve the old canonical name as UserCollege.display_name '
                                 'when IPEDS renames a college (default: on).')

    def handle(self, *args, **opts):
        rows = self._load_csv(opts['csv'])
        self._validate_aliases(rows)

        manual = {}
        if opts['matches'] and os.path.exists(opts['matches']):
            with open(opts['matches'], newline='', encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    manual[norm(r['name'])] = r['unitid'].strip()

        matcher = Matcher(rows)
        by_unitid = {r['unitid']: r for r in rows if r['unitid']}

        existing = list(College.objects.all())
        adopted, ambiguous, unmatched_db, conflicts = [], [], [], []
        claimed = {}   # id(csv row) -> College that claimed it

        def claim(col, row, how):
            """Bind col to row unless another college already took it.

            Two colleges resolving to one CSV row would collide on the unique
            unitid. That means a duplicate in the College table, which is a
            merge, not an import — so report it instead.
            """
            owner = claimed.get(id(row))
            if owner is not None:
                conflicts.append((col, row, owner))
                return
            claimed[id(row)] = col
            adopted.append((col, row, how))

        for col in existing:
            # A unitid is identity. Matching those by name again is what made
            # a second run try to re-adopt (and duplicate) everything.
            if col.unitid:
                hit = by_unitid.get(col.unitid)
                if hit:
                    claim(col, hit, 'unitid')
                else:
                    unmatched_db.append((col, f'unitid {col.unitid} no longer in CSV'))
                continue

            key = norm(col.name)
            if key in manual:
                hit = by_unitid.get(manual[key])
                if hit:
                    claim(col, hit, 'manual')
                else:
                    unmatched_db.append((col, f'manual unitid {manual[key]!r} not in CSV'))
                continue

            hit, info = matcher.match(col.name)
            if hit:
                claim(col, hit, info)
            elif info:
                ambiguous.append((col, info))
            else:
                unmatched_db.append((col, 'no candidate in CSV'))

        new_rows = [r for r in rows if id(r) not in claimed]

        self._report(adopted, ambiguous, unmatched_db, new_rows, conflicts)

        if opts['dry_run']:
            self.stdout.write(self.style.WARNING('\n--dry-run: nothing written.'))
            return

        if conflicts:
            raise SystemExit(
                '\nRefusing to write: the colleges above are duplicates competing for the '
                'same IPEDS row. Merge them first (repoint the UserCollege rows and delete '
                'the loser), then re-run.'
            )

        with transaction.atomic():
            renamed = 0
            for col, row, _method in adopted:
                old_name = col.name
                self._apply(col, row)
                col.save()
                if opts['keep_display_names'] and old_name != col.name:
                    renamed += self._preserve_display_name(col, old_name)
            created = 0
            for row in new_rows:
                col = College(unitid=row['unitid'] or None, name=row['name'])
                self._apply(col, row)
                col.save()
                created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nUpdated {len(adopted)} existing colleges (pks preserved), created {created} new.'
        ))
        if renamed:
            self.stdout.write(
                f'Preserved {renamed} of your names as UserCollege.display_name '
                f'(e.g. "Caltech" still reads Caltech). Clear display_name to show the IPEDS name.'
            )
        if ambiguous or unmatched_db:
            self.stdout.write(self.style.WARNING(
                f'{len(ambiguous) + len(unmatched_db)} colleges left unlinked — see the report above. '
                f'Resolve with: --matches file.csv (college_id,unitid)'
            ))

    # ------------------------------------------------------------------ #

    def _load_csv(self, path):
        with open(path, newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            r['name'] = r['name'].strip()
            r['unitid'] = r['unitid'].strip()
            r['_n'] = norm(r['name'])
            r['_stem'] = strip_suffix(r['_n'])
            r['_proof'] = to_int(r['proof_acceptances']) or 0
        return rows

    def _validate_aliases(self, rows):
        names = {r['name'] for r in rows}
        broken = sorted(v for v in ALIASES.values() if v not in names)
        if broken:
            raise SystemExit(
                'Aliases point at CSV names that do not exist:\n  ' + '\n  '.join(broken)
            )

    def _apply(self, col, row):
        """Copy IPEDS facts onto a College. Never touches fields the CSV lacks
        (sat_avg, app_platform, deadlines)."""
        col.unitid = row['unitid'] or None
        col.name = row['name']
        col.city = row['city'] or ''
        col.state = row['state'] or ''
        col.country = row['country'] or ''
        col.latitude = to_float(row['latitude'])
        col.longitude = to_float(row['longitude'])
        col.tuition_instate = to_int(row['tuition_instate'])
        col.fees_instate = to_int(row['fees_instate'])
        col.tuition_outofstate = to_int(row['tuition_outofstate'])
        col.fees_outofstate = to_int(row['fees_outofstate'])
        col.room = to_int(row['room'])
        col.board = to_int(row['board'])
        col.total_cost = to_int(row['total_cost_tuition_fees_room_board'])
        col.avg_grant_aid = to_int(row['avg_grant_aid'])
        col.academic_calendar = row['academic_calendar'] or ''
        col.acceptance_rate = row['acceptance_rate'] or ''
        col.undergrad_enrollment = to_int(row['undergrad_enrollment'])
        col.proof_acceptances = row['_proof']

    def _preserve_display_name(self, col, old_name):
        """Keep the user's shorthand visible after an IPEDS rename."""
        n = 0
        for uc in col.user_colleges.filter(display_name=''):
            uc.display_name = old_name
            uc.save(update_fields=['display_name'])
            n += 1
        return n

    def _report(self, adopted, ambiguous, unmatched_db, new_rows, conflicts=()):
        from collections import Counter
        methods = Counter(m for _, _, m in adopted)
        w = self.stdout.write
        w(self.style.MIGRATE_HEADING('\n=== MATCH REPORT ==='))
        w(f'Existing colleges matched : {len(adopted)}  {dict(methods)}')
        w(f'New colleges to create    : {len(new_rows)}')
        w(f'Ambiguous (left alone)    : {len(ambiguous)}')
        w(f'Unmatched (left alone)    : {len(unmatched_db)}')
        if conflicts:
            w(self.style.ERROR(f'Duplicate collisions       : {len(conflicts)}'))
            for col, row, owner in conflicts:
                w(self.style.ERROR(
                    f'  id={col.pk} {col.name!r} wants {row["name"]!r} ({row["unitid"]}), '
                    f'already claimed by id={owner.pk} {owner.name!r}'
                ))

        inferred = [(c, r, m) for c, r, m in adopted if m not in ('exact', 'normalized', 'stem')]
        if inferred:
            w(self.style.MIGRATE_HEADING('\n--- matched by alias/prefix (review these) ---'))
            for col, row, m in sorted(inferred, key=lambda x: x[0].name):
                w(f'  [{m:18s}] {col.name!r} -> {row["name"]!r} ({row["unitid"] or "no unitid"})')

        if ambiguous:
            w(self.style.WARNING('\n--- AMBIGUOUS: resolve by hand (college_id,unitid) ---'))
            for col, cands in ambiguous:
                w(f'  id={col.pk} {col.name!r}')
                for r in cands:
                    w(f'      {r["unitid"] or "-":8s} {r["name"]!r} {r["state"]} proof={r["_proof"]}')

        if unmatched_db:
            w(self.style.WARNING('\n--- UNMATCHED: not in the CSV, staying custom ---'))
            for col, why in unmatched_db:
                w(f'  id={col.pk} {col.name!r} ({why})')
