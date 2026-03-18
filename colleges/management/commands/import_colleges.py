import csv
from django.core.management.base import BaseCommand
from colleges.models import College


# Map Jacob's idiosyncratic Apply? values to standardized choices
APPLY_STATUS_MAP = {
    'yes': 'applying',
    'probably': 'likely',
    'maybe': 'considering',
    'imaginably': 'considering',
    'doubtful': 'unlikely',
    'done': 'not_applying',
    'accepted': 'accepted',
    'waitlisted': 'waitlisted',
    'rejected': 'rejected',
    '5': 'applying',
    '4': 'likely',
    '3': 'considering',
    '2': 'considering',
    '1': 'unlikely',
}


class Command(BaseCommand):
    help = 'Import colleges from the College List CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)
        parser.add_argument('--clear', action='store_true', help='Clear existing colleges before import')

    def handle(self, *args, **options):
        if options['clear']:
            College.objects.all().delete()
            self.stdout.write('Cleared existing colleges.')

        with open(options['csv_file'], newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header row

            count = 0
            for i, row in enumerate(reader):
                name = row[0].strip() if row[0] else ''
                if not name or name.startswith('(delete'):
                    continue

                apply_raw = row[1].strip().lower() if len(row) > 1 else ''
                apply_status = APPLY_STATUS_MAP.get(apply_raw, '')

                college = College(
                    name=name,
                    apply_status=apply_status,
                    tier=row[2].strip() if len(row) > 2 else '',
                    acceptance_rate=row[3].strip() if len(row) > 3 else '',
                    collegevine_chance=row[4].strip() if len(row) > 4 else '',
                    location=row[5].strip() if len(row) > 5 else '',
                    app_platform=row[6].strip() if len(row) > 6 else '',
                    terms=row[7].strip() if len(row) > 7 else '',
                    cost_of_attendance=row[8].strip() if len(row) > 8 else '',
                    requirements_style=row[9].strip() if len(row) > 9 else '',
                    restrictive_ea=row[10].strip() if len(row) > 10 else '',
                    ea_deadline=row[11].strip() if len(row) > 11 else '',
                    ed1_deadline=row[12].strip() if len(row) > 12 else '',
                    ed2_deadline=row[13].strip() if len(row) > 13 else '',
                    rd_deadline=row[14].strip() if len(row) > 14 else '',
                    other_deadline=row[15].strip() if len(row) > 15 else '',
                    self_report_sat=row[16].strip() if len(row) > 16 else '',
                    interview=row[17].strip() if len(row) > 17 else '',
                    known_students=row[18].strip() if len(row) > 18 else '',
                    known_faculty=row[19].strip() if len(row) > 19 else '',
                    intended_major=row[20].strip() if len(row) > 20 else '',
                    second_choice_major=row[21].strip() if len(row) > 21 else '',
                    third_choice_major=row[22].strip() if len(row) > 22 else '',
                    toured=row[23].strip() if len(row) > 23 else '',
                    portal_info=row[24].strip() if len(row) > 24 else '',
                    applicant_notes=row[25].strip() if len(row) > 25 else '',
                    parent_notes=row[26].strip() if len(row) > 26 else '',
                    random_notes=row[27].strip() if len(row) > 27 else '',
                    order=i,
                )
                college.save()
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {count} colleges.'))
