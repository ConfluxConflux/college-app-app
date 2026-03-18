import csv
from django.core.management.base import BaseCommand
from activities.models import UCEntry, CommonAppActivity, CommonAppHonor, MITEntry
from core.models import CoreActivity


def is_data_row(row):
    """Check if a row has actual data (not a header, instruction, or empty row)."""
    first = row[0].strip() if row[0] else ''
    if not first:
        return False
    if first.startswith('DELETE'):
        return False
    if first.startswith('ONLY'):
        return False
    return True


def has_x(val):
    """Check if a cell contains 'X' (grade level marker)."""
    return val.strip().upper() == 'X' if val else False


# Map CSV activity type display names to model choice keys
COMMON_APP_TYPE_MAP = {
    'journalism/publication': 'journalism_publication',
    'community service (volunteer)': 'community',
    'academic': 'academic',
    'art': 'art',
    'athletics: club': 'athletics_club',
    'athletics: jv/varsity': 'athletics_jv_varsity',
    'career oriented': 'career',
    'computer/technology': 'computer_technology',
    'cultural': 'cultural',
    'dance': 'dance',
    'debate/speech': 'debate_speech',
    'environmental': 'environmental',
    'family responsibilities': 'family_responsibilities',
    'foreign exchange': 'foreign_exchange',
    "junior r.o.t.c.": 'junior_rotc',
    'lgbt': 'lgbtq',
    'music: instrumental': 'music_instrumental',
    'music: vocal': 'music_vocal',
    'religious': 'religious',
    'research': 'research',
    'robotics': 'robotics',
    'school spirit': 'school_spirit',
    'science/math': 'science_math',
    "student govt./politics": 'student_govt',
    'theater/drama': 'theater_drama',
    'work (paid)': 'work_paid',
    'other club/activity': 'other',
}

UC_CATEGORY_MAP = {
    'award or honor': 'award',
    'educational preparation program': 'edu_prep',
    'extracurricular activity': 'extracurricular',
    'volunteer / community service': 'volunteer',
    'work experience': 'work',
    'other coursework': 'coursework',
}

MIT_CATEGORY_MAP = {
    'job': 'job',
    'activity': 'activity',
    '"summer activity"': 'summer',
    'summer activity': 'summer',
    'scholastic distinction': 'scholastic',
    'non-scholastic distinction': 'non_scholastic',
}


class Command(BaseCommand):
    help = 'Import activities from CSV files (UC, Common App, Honors, MIT)'

    def add_arguments(self, parser):
        parser.add_argument('--uc', type=str, help='UC Activities & Awards CSV')
        parser.add_argument('--activities', type=str, help='Common App Activities CSV')
        parser.add_argument('--honors', type=str, help='Common App Honors CSV')
        parser.add_argument('--mit', type=str, help='MIT J&A&D CSV')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before import')

    def handle(self, *args, **options):
        if options['clear']:
            UCEntry.objects.all().delete()
            CommonAppActivity.objects.all().delete()
            CommonAppHonor.objects.all().delete()
            MITEntry.objects.all().delete()
            CoreActivity.objects.all().delete()
            self.stdout.write('Cleared existing activities.')

        if options.get('uc'):
            self.import_uc(options['uc'])
        if options.get('activities'):
            self.import_common_app(options['activities'])
        if options.get('honors'):
            self.import_honors(options['honors'])
        if options.get('mit'):
            self.import_mit(options['mit'])

    def get_or_create_hub(self, name):
        """Find or create a CoreActivity hub entry by name."""
        if not name:
            return None
        # Try to find an existing hub with a similar name
        hub = CoreActivity.objects.filter(name__iexact=name).first()
        if not hub:
            hub = CoreActivity.objects.create(name=name)
        return hub

    def import_uc(self, filepath):
        count = 0
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Data rows start after the instruction rows (row index 10+)
        for i, row in enumerate(rows):
            if i < 10:  # Skip header/instruction rows
                continue
            if not is_data_row(row):
                continue

            name = row[0].strip()
            category_raw = row[1].strip().lower() if len(row) > 1 else ''
            category = UC_CATEGORY_MAP.get(category_raw, '')
            if not category:
                continue

            hub = self.get_or_create_hub(name.split('//')[0].strip())

            entry = UCEntry(
                core_activity=hub,
                order=count,
                category=category,
                name=name,
                background=row[2].strip() if len(row) > 2 and row[2].strip() != '–' else '',
                description=row[3].strip() if len(row) > 3 else '',
                grade_9=has_x(row[5]) if len(row) > 5 else False,
                grade_10=has_x(row[6]) if len(row) > 6 else False,
                grade_11=has_x(row[7]) if len(row) > 7 else False,
                grade_12=has_x(row[8]) if len(row) > 8 else False,
                hours_per_week=row[10].strip() if len(row) > 10 and row[10].strip() != '–' else '',
                weeks_per_year=row[11].strip() if len(row) > 11 and row[11].strip() != '–' else '',
                personal_notes=row[17].strip() if len(row) > 17 else '',
            )

            # Category-specific fields
            if category == 'award':
                entry.recognition_level = row[13].strip() if len(row) > 13 else ''
                is_acad = row[15].strip().lower() if len(row) > 15 else ''
                entry.is_academic = True if is_acad == 'yes' else (False if is_acad == 'no' else None)
            elif category == 'work':
                entry.earnings_usage = row[13].strip() if len(row) > 13 else ''
                still = row[15].strip().lower() if len(row) > 15 else ''
                entry.still_working = True if still == 'yes' else (False if still == 'no' else None)

            entry.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {count} UC entries.'))

    def import_common_app(self, filepath):
        count = 0
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        for i, row in enumerate(rows):
            if i < 4:  # Skip header rows
                continue
            if not is_data_row(row):
                continue
            # Stop at the "ONLY 10" instruction or "Your plans" section
            first = row[0].strip()
            if first.startswith('ONLY') or first.startswith('Your plans'):
                continue

            type_raw = row[0].strip().lower() if row[0] else ''
            activity_type = COMMON_APP_TYPE_MAP.get(type_raw, 'other')

            org = row[2].strip() if len(row) > 2 else ''
            hub = self.get_or_create_hub(org) if org else None

            def parse_int(val):
                try:
                    return int(val.strip())
                except (ValueError, AttributeError):
                    return None

            entry = CommonAppActivity(
                core_activity=hub,
                order=count,
                activity_type=activity_type,
                position=row[1].strip() if len(row) > 1 else '',
                organization=org,
                description=row[4].strip() if len(row) > 4 else '',
                grade_9=has_x(row[6]) if len(row) > 6 else False,
                grade_10=has_x(row[7]) if len(row) > 7 else False,
                grade_11=has_x(row[8]) if len(row) > 8 else False,
                grade_12=has_x(row[9]) if len(row) > 9 else False,
                timing_school=has_x(row[11]) if len(row) > 11 else False,
                timing_breaks=has_x(row[12]) if len(row) > 12 else False,
                timing_all_year=has_x(row[13]) if len(row) > 13 else False,
                hours_per_week=parse_int(row[15]) if len(row) > 15 else None,
                weeks_per_year=parse_int(row[16]) if len(row) > 16 else None,
                similar_in_college=(
                    row[18].strip().lower() == 'yes' if len(row) > 18 and row[18].strip() else None
                ),
                personal_notes=row[20].strip() if len(row) > 20 else '',
            )
            entry.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {count} Common App activities.'))

    def import_honors(self, filepath):
        count = 0
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        for i, row in enumerate(rows):
            if i < 4:  # Skip header rows
                continue
            if not is_data_row(row):
                continue

            title = row[0].strip()
            if not title:
                continue

            hub = self.get_or_create_hub(title)

            entry = CommonAppHonor(
                core_activity=hub,
                order=count,
                title=title,
                grade_9=has_x(row[2]) if len(row) > 2 else False,
                grade_10=has_x(row[3]) if len(row) > 3 else False,
                grade_11=has_x(row[4]) if len(row) > 4 else False,
                grade_12=has_x(row[5]) if len(row) > 5 else False,
                level_school=has_x(row[7]) if len(row) > 7 else False,
                level_state_regional=has_x(row[8]) if len(row) > 8 else False,
                level_national=has_x(row[9]) if len(row) > 9 else False,
                level_international=has_x(row[10]) if len(row) > 10 else False,
                personal_notes=row[12].strip() if len(row) > 12 else '',
            )
            entry.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {count} Common App honors.'))

    def import_mit(self, filepath):
        count = 0
        with open(filepath, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        for i, row in enumerate(rows):
            if i < 2:  # Skip header rows
                continue
            if not is_data_row(row):
                continue

            category_raw = row[0].strip().lower() if row[0] else ''
            category = MIT_CATEGORY_MAP.get(category_raw, '')
            if not category:
                continue

            org_name = row[1].strip() if len(row) > 1 else ''
            if not org_name:
                continue

            hub = self.get_or_create_hub(org_name)

            def parse_int(val):
                try:
                    return int(val.strip())
                except (ValueError, AttributeError):
                    return None

            entry = MITEntry(
                core_activity=hub,
                order=count,
                category=category,
                org_name=org_name,
                role_award=row[2].strip() if len(row) > 2 else '',
                participation_period=row[3].strip() if len(row) > 3 else '',
                hours_per_week=parse_int(row[4]) if len(row) > 4 else None,
                weeks_per_year=parse_int(row[5]) if len(row) > 5 else None,
                description=row[6].strip() if len(row) > 6 else '',
                personal_notes=row[7].strip() if len(row) > 7 else '',
            )
            entry.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Imported {count} MIT entries.'))
