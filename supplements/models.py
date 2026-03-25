from django.db import models


UC_PIQ_PROMPTS = [
    "Describe an example of your leadership experience in which you have positively influenced others, helped resolve disputes, or contributed to group efforts over time.",
    "Every person has a creative side, and it can be expressed in many ways: problem solving, original and innovative thinking, and/or in art, writing, music, dance, theater, etc. Describe how you express your creative side.",
    "What would you say is your greatest talent or skill? How have you developed and demonstrated that talent over time?",
    "Describe how you have taken advantage of a significant educational opportunity or worked to overcome an educational barrier you have faced.",
    "Describe the most significant challenge you have faced and the steps you have taken to overcome this challenge. How has this challenge affected your academic achievement?",
    "Think about an academic subject that inspires you. Describe how you have furthered this interest inside and/or outside of the classroom.",
    "What have you done to make your school or your community a better place?",
    "Beyond what has already been shared in your application, what do you believe makes you stand out as a strong candidate for admission to the University of California?",
]

COMMON_APP_PROMPTS = [
    "Some students have a background, identity, interest, or talent that is so meaningful they believe their application would be incomplete without it. If this sounds like you, then please share your story.",
    "The lessons we take from obstacles we encounter can be fundamental to later success. Recount a time when you faced a challenge, setback, or failure. How did it affect you, and what did you learn from the experience?",
    "Reflect on a time when you questioned or challenged a belief or idea. What prompted your thinking? What was the outcome?",
    "Reflect on something that someone has done for you that has made you happy or thankful in a surprising way. How has this gratitude affected or motivated you?",
    "Discuss an accomplishment, event, or realization that sparked a period of personal growth and a new understanding of yourself or others.",
    "Describe a topic, idea, or concept you find so engaging that it makes you lose all track of time. Why does it captivate you? What or who do you turn to when you want to learn more?",
    "Share an essay on any topic of your choice. It can be one you've already written, one that responds to a different prompt, or one of your own design.",
]


class EssayCategory(models.Model):
    """Thematic category for grouping essays across colleges."""
    name = models.CharField(max_length=200)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'essay categories'

    def __str__(self):
        return self.name


class SupplementEssay(models.Model):
    """One essay prompt+response for one college."""
    STATUS_CHOICES = [
        ('', '—'),
        ('wip', 'WIP'),
        ('done', 'Done'),
        ('maybe', 'Maybe'),
    ]

    applicant = models.ForeignKey(
        'core.Applicant', null=True, blank=True,
        on_delete=models.CASCADE, related_name='essays'
    )
    college = models.ForeignKey(
        'colleges.College', on_delete=models.CASCADE,
        related_name='essays'
    )
    category = models.ForeignKey(
        EssayCategory, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='essays'
    )
    prompt = models.TextField(blank=True)
    word_limit = models.IntegerField(null=True, blank=True)
    char_limit = models.IntegerField(null=True, blank=True)
    response = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True)
    notes = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        college_name = self.college.name if self.college else '?'
        category_name = self.category.name if self.category else 'Uncategorized'
        return f'{college_name} - {category_name}'

    @property
    def word_count(self):
        if not self.response:
            return 0
        return len(self.response.split())

    @property
    def char_count(self):
        return len(self.response)

    @property
    def status_color(self):
        return {
            'wip': 'is-warning',
            'done': 'is-success',
            'maybe': 'is-info',
        }.get(self.status, '')


class UCPersonalInsightQuestion(models.Model):
    STATUS_CHOICES = [
        ('', '—'),
        ('wip', 'WIP'),
        ('done', 'Done'),
        ('maybe', 'Maybe'),
    ]

    applicant = models.ForeignKey(
        'core.Applicant', on_delete=models.CASCADE, related_name='uc_piqs'
    )
    question_number = models.IntegerField()  # 1–8
    response = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True)

    class Meta:
        unique_together = [['applicant', 'question_number']]
        ordering = ['question_number']

    @property
    def prompt(self):
        return UC_PIQ_PROMPTS[self.question_number - 1]

    @property
    def word_count(self):
        return len(self.response.split()) if self.response.strip() else 0

    @property
    def progress_pct(self):
        return min(int(self.word_count / 350 * 100), 100)


class CommonAppEssay(models.Model):
    STATUS_CHOICES = [
        ('', '—'),
        ('wip', 'WIP'),
        ('done', 'Done'),
        ('maybe', 'Maybe'),
    ]

    applicant = models.OneToOneField(
        'core.Applicant', on_delete=models.CASCADE, related_name='common_app_essay'
    )
    prompt_choice = models.IntegerField(null=True, blank=True)  # 1–7; null = not chosen
    response = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, blank=True)

    @property
    def prompt(self):
        if self.prompt_choice:
            return COMMON_APP_PROMPTS[self.prompt_choice - 1]
        return None

    @property
    def word_count(self):
        return len(self.response.split()) if self.response.strip() else 0

    @property
    def progress_pct(self):
        return min(int(self.word_count / 650 * 100), 100)
