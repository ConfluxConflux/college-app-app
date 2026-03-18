import csv
from django.core.management.base import BaseCommand
from supplements.models import EssayCategory, SupplementEssay
from colleges.models import College


class Command(BaseCommand):
    help = 'Import supplemental essays from the Supplementals At A Glance CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str)
        parser.add_argument('--clear', action='store_true', help='Clear existing data before import')

    def handle(self, *args, **options):
        if options['clear']:
            SupplementEssay.objects.all().delete()
            EssayCategory.objects.all().delete()
            self.stdout.write('Cleared existing supplements.')

        with open(options['csv_file'], newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        if len(rows) < 3:
            self.stdout.write(self.style.ERROR('CSV too short.'))
            return

        # Row 0: title row (skip)
        # Row 1: headers - "Essay Category, Sort, Heading, MIT, Stanford, Reed, ..."
        header = rows[1]
        college_names = [h.strip() for h in header[3:] if h.strip()]

        # Get or create College objects for the supplement colleges
        college_map = {}
        for cname in college_names:
            college = College.objects.filter(name__icontains=cname).first()
            if not college:
                college = College.objects.create(name=cname)
                self.stdout.write(f'Created college: {cname}')
            college_map[cname] = college

        # Row 2: Status row - overall status per college
        status_row = rows[2]

        # Parse categories and their prompt/response/status sub-rows
        # Structure: category rows come in groups where Heading is Prompt/Response/Status
        current_category = None
        current_sort = 0
        essay_count = 0

        for row in rows[3:]:
            if len(row) < 3:
                continue

            cat_name = row[0].strip()
            sort_val = row[1].strip()
            heading = row[2].strip()

            if cat_name:
                # This row introduces a new category
                try:
                    current_sort = int(sort_val) if sort_val else current_sort + 1
                except ValueError:
                    current_sort += 1

                current_category, _ = EssayCategory.objects.get_or_create(
                    name=cat_name,
                    defaults={'sort_order': current_sort}
                )

            if not current_category:
                continue

            # For each college column, populate essays
            if heading.lower() == 'prompt':
                for j, cname in enumerate(college_names):
                    col_idx = 3 + j
                    prompt_text = row[col_idx].strip() if col_idx < len(row) else ''
                    if prompt_text and prompt_text != '—':
                        # Parse word limit from prompt if present, e.g. "(250)"
                        word_limit = None
                        if '(' in prompt_text and ')' in prompt_text:
                            paren_content = prompt_text[prompt_text.rfind('(') + 1:prompt_text.rfind(')')]
                            try:
                                word_limit = int(paren_content)
                            except ValueError:
                                pass

                        essay, created = SupplementEssay.objects.get_or_create(
                            college=college_map[cname],
                            category=current_category,
                            defaults={
                                'prompt': prompt_text,
                                'word_limit': word_limit,
                                'sort_order': current_sort,
                            }
                        )
                        if not created:
                            essay.prompt = prompt_text
                            if word_limit:
                                essay.word_limit = word_limit
                            essay.save()
                        essay_count += 1

            elif heading.lower() == 'response':
                for j, cname in enumerate(college_names):
                    col_idx = 3 + j
                    response_text = row[col_idx].strip() if col_idx < len(row) else ''
                    if response_text and response_text != '—':
                        essay = SupplementEssay.objects.filter(
                            college=college_map[cname],
                            category=current_category,
                        ).first()
                        if essay:
                            essay.response = response_text
                            essay.save()
                        else:
                            SupplementEssay.objects.create(
                                college=college_map[cname],
                                category=current_category,
                                response=response_text,
                                sort_order=current_sort,
                            )

            elif heading.lower() == 'status':
                for j, cname in enumerate(college_names):
                    col_idx = 3 + j
                    status_text = row[col_idx].strip().lower() if col_idx < len(row) else ''
                    status = ''
                    if status_text in ('wip', 'work in progress'):
                        status = 'wip'
                    elif status_text == 'done':
                        status = 'done'
                    elif status_text == 'maybe':
                        status = 'maybe'

                    if status:
                        essay = SupplementEssay.objects.filter(
                            college=college_map[cname],
                            category=current_category,
                        ).first()
                        if essay:
                            essay.status = status
                            essay.save()

            elif not heading:
                # Row with just a category name and data in college columns
                # (like "Personal Essay" row which has direct responses)
                for j, cname in enumerate(college_names):
                    col_idx = 3 + j
                    text = row[col_idx].strip() if col_idx < len(row) else ''
                    if text and text != '—':
                        essay, created = SupplementEssay.objects.get_or_create(
                            college=college_map[cname],
                            category=current_category,
                            defaults={
                                'response': text,
                                'sort_order': current_sort,
                            }
                        )
                        if not created and not essay.response:
                            essay.response = text
                            essay.save()
                        if created:
                            essay_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Imported {EssayCategory.objects.count()} categories, {essay_count} essays.'
        ))
