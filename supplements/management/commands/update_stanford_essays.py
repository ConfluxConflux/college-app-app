"""
Fix Stanford supplemental essay data:
  1. Split pk=8 (currently combines two 50w prompts) into separate essays
  2. Fix pk=3 category (Major/Academics → Learning/Semi-Why Us)
  3. Set correct Stanford prompt text for all essays
  4. Set pk=1 (Personal Essay) word limit and sort order
"""
from django.core.management.base import BaseCommand
from supplements.models import EssayCategory, SupplementEssay
from colleges.models import UserCollege


class Command(BaseCommand):
    help = 'Fix Stanford supplemental essay data'

    def handle(self, *args, **options):
        stanford = UserCollege.objects.filter(college__name__icontains='stanford').first()
        if not stanford:
            self.stdout.write(self.style.ERROR('Stanford not found in DB.'))
            return

        cat_learning = EssayCategory.objects.get(name='Learning / Semi-Why Us')
        cat_activities = EssayCategory.objects.get(name='Activities')

        # ── pk=1: Personal Essay (Common App, submitted as part of Stanford application) ──
        e1 = SupplementEssay.objects.get(pk=1)
        e1.word_limit = 650
        e1.sort_order = 0
        e1.prompt = (
            'The Common App personal statement is submitted as part of the Stanford application. '
            'Stanford does not prescribe a topic — choose any of the seven Common App prompts '
            'or write on a topic of your choice. (650 words)'
        )
        e1.save()
        self.stdout.write('Updated pk=1 (Personal Essay)')

        # ── pk=3: Reflect on learning — fix category ──
        e3 = SupplementEssay.objects.get(pk=3)
        e3.category = cat_learning
        e3.word_limit = 250
        e3.sort_order = 10
        e3.prompt = (
            'Reflect on an idea or experience that makes you genuinely excited about learning. '
            '(250 words)'
        )
        e3.save()
        self.stdout.write('Updated pk=3 (Learning essay, fixed category)')

        # ── pk=6: Describe what aspects of your life… ──
        e6 = SupplementEssay.objects.get(pk=6)
        e6.word_limit = 250
        e6.sort_order = 20
        e6.prompt = (
            'Please describe what aspects of your life experiences, interests and character '
            'would most help us to understand you and, if admitted, your intended contribution '
            'to the Stanford community. (250 words)'
        )
        e6.save()
        self.stdout.write('Updated pk=6 (Lived Experience essay)')

        # ── pk=8: Split into "Last two summers" + "Extracurricular elaborate" ──
        e8 = SupplementEssay.objects.get(pk=8)
        e8.category = cat_activities
        e8.word_limit = 50
        e8.sort_order = 30
        e8.prompt = 'How did you spend your last two summers? (50 words)'
        e8.save()
        self.stdout.write('Updated pk=8 (Last two summers)')

        # Create the split-off extracurricular essay if it doesn't already exist
        ec_essay, created = SupplementEssay.objects.get_or_create(
            college=stanford,
            category=cat_activities,
            sort_order=31,
            defaults={
                'prompt': (
                    'Briefly elaborate on one of your extracurricular activities '
                    'or work experiences. (50 words)'
                ),
                'word_limit': 50,
            }
        )
        if not created:
            ec_essay.prompt = (
                'Briefly elaborate on one of your extracurricular activities '
                'or work experiences. (50 words)'
            )
            ec_essay.word_limit = 50
            ec_essay.save()
        self.stdout.write(f'{"Created" if created else "Updated"} extracurricular elaborate essay (pk={ec_essay.pk})')

        # ── pk=13: Five things ──
        e13 = SupplementEssay.objects.get(pk=13)
        e13.word_limit = 50
        e13.sort_order = 40
        e13.prompt = 'List five things that are important to you. (50 words)'
        e13.save()
        self.stdout.write('Updated pk=13 (Five things)')

        # ── pk=14: Significant challenge ──
        e14 = SupplementEssay.objects.get(pk=14)
        e14.word_limit = 50
        e14.sort_order = 50
        e14.prompt = 'What is the most significant challenge that society faces today? (50 words)'
        e14.save()
        self.stdout.write('Updated pk=14 (Society challenge)')

        # ── pk=15: Roommate note ──
        e15 = SupplementEssay.objects.get(pk=15)
        e15.word_limit = 250
        e15.sort_order = 60
        e15.prompt = (
            'Write a note to your future roommate that reveals something about you or that '
            'will help your roommate — and us — know you better. (250 words)'
        )
        e15.save()
        self.stdout.write('Updated pk=15 (Roommate note)')

        # ── pk=16: Historical moment ──
        e16 = SupplementEssay.objects.get(pk=16)
        e16.word_limit = 50
        e16.sort_order = 70
        e16.prompt = (
            'What historical moment or event do you wish you could have witnessed? (50 words)'
        )
        e16.save()
        self.stdout.write('Updated pk=16 (Historical moment)')

        self.stdout.write(self.style.SUCCESS('Done — Stanford essays updated.'))
