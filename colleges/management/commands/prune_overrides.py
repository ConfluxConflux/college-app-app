"""Drop UserCollege overrides that IPEDS now supersedes.

Migration 0008 renamed the old College table into UserCollege, so every value
Jacob had landed in a *_override column. Overrides shadow canonical data by
design, which means the IPEDS import changes nothing on screen until the
redundant ones are cleared. The model intends overrides to be sparse: present
only where a user deliberately disagrees with a canonical fact.

Two rules, both conservative:

  * Never clear an override with no canonical value behind it — there would be
    nothing to fall back to and the data would just be gone.
  * For academic_calendar, only clear overrides that already agree with IPEDS.
    Where they disagree the override is sometimes better than IPEDS ('IAP +
    Semester' vs '4-1-4') and sometimes wrong (Reed is a semester school).
    Telling those apart is a judgement call, so they are reported, not deleted.

app_platform_override is deliberately untouched: canonical College.app_platform
is empty for every row, so clearing it would blank every platform and break the
tracker. It stays the only platform data there is until a real Common App
member list is imported.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from colleges.models import UserCollege

# field -> whether to clear only when the override already matches canonical
FIELDS = {
    'acceptance_rate': False,      # IPEDS is strictly better: yours are stale roundings
    'academic_calendar': True,     # only clear exact agreements
}


def norm(v):
    return (v or '').strip().lower()


class Command(BaseCommand):
    help = 'Clear UserCollege overrides that IPEDS canonical data supersedes.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would be cleared; write nothing.')

    def handle(self, *args, **opts):
        w = self.stdout.write
        to_clear = []   # (obj, field, old, canonical)
        kept = []       # (obj, field, old, canonical, why)

        qs = UserCollege.objects.select_related('college').all()
        for uc in qs:
            for field, only_if_equal in FIELDS.items():
                old = getattr(uc, field + '_override')
                if not old and old != 0:
                    continue
                canonical = getattr(uc.college, field, None) if uc.college_id else None
                if not norm(canonical):
                    kept.append((uc, field, old, canonical, 'no canonical value to fall back on'))
                    continue
                if only_if_equal and norm(old) != norm(canonical):
                    kept.append((uc, field, old, canonical, 'differs from IPEDS — your call'))
                    continue
                to_clear.append((uc, field, old, canonical))

        w(self.style.MIGRATE_HEADING('\n=== OVERRIDE PRUNE ==='))
        w(f'Would clear : {len(to_clear)}')
        w(f'Keeping     : {len(kept)}')

        by_field = {}
        for _, f, _, _ in to_clear:
            by_field[f] = by_field.get(f, 0) + 1
        for f, n in sorted(by_field.items()):
            w(f'    clear {f + "_override":28s} {n}')

        if kept:
            w(self.style.WARNING('\n--- KEPT (review; clear by hand if IPEDS is right) ---'))
            for uc, f, old, canonical, why in sorted(kept, key=lambda k: (k[1], str(k[0].name))):
                w(f'  [{f}] {str(uc.name)[:30]:32s} yours={old!r:16s} ipeds={canonical!r:12s} {why}')

        if opts['dry_run']:
            w(self.style.WARNING('\n--dry-run: nothing written.'))
            return

        with transaction.atomic():
            for uc, field, _old, _canon in to_clear:
                setattr(uc, field + '_override', '')
                uc.save(update_fields=[field + '_override'])

        w(self.style.SUCCESS(f'\nCleared {len(to_clear)} overrides; canonical IPEDS values now show through.'))
