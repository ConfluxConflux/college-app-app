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


# One vocabulary for every kind of essay — supplements, UC PIQs, the Common App
# essay — so a pill means the same thing wherever it appears.
#
# The 'wip' and 'done' keys are deliberately unchanged: the dashboard and the
# applications page count status='done', and renaming the key would silently
# zero those without breaking anything loudly enough to notice.
ESSAY_STATUS_CHOICES = [
    ('todo', 'To Do'),
    ('idea', 'Idea Stage'),
    ('wip', 'WIP'),
    ('drafted', 'Drafted'),
    ('done', 'DONE'),
]


# Seeded for every new applicant, then theirs to change. Jacob's original
# taxonomy makes a reasonable starting vocabulary, but people group essays the
# way they think about them, so nobody is stuck with it.
DEFAULT_ESSAY_TAGS = [
    'Personal Essay',
    'Major / Academics',
    'Learning / Semi-Why Us',
    'Lived Experience / World / Diversity',
    'Activities',
    'Community / Diversity',
    'Why Us',
    'Personal Challenge',
    # Common enough to be its own row rather than living in Catchall: "a time
    # you disagreed", "engage with a view unlike your own", "a conversation
    # that changed your mind" are the same essay at a dozen schools.
    'Disagreement / Respectful Dialogue',
    'Inspiration / Joy / Philosophical',
    'Future / Global Challenge',
    'Quirky / Misc',
    # The 25-to-50-word questions the Ivies stack up — favourite word, what you
    # do for fun, a book you'd bring. They group by length, not topic: the work
    # of writing one is nothing like a 650-word essay.
    'Short Take',
    'Hypothetical',
    'Catchall',
    'Other',
]


class EssayCategory(models.Model):
    """A tag for grouping essays across colleges. Owned by one applicant.

    Per-applicant rather than shared: the tags are what drive the By Topic
    view, and their whole job is to reflect how *this* person sees their
    essays. A global list meant renaming one renamed it for everyone.
    """
    applicant = models.ForeignKey(
        'core.Applicant', null=True, blank=True,
        on_delete=models.CASCADE, related_name='essay_tags'
    )
    name = models.CharField(max_length=200)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'essay categories'
        constraints = [
            models.UniqueConstraint(
                fields=['applicant', 'name'], name='unique_tag_name_per_applicant'
            )
        ]

    def __str__(self):
        return self.name


def ensure_default_tags(applicant):
    """Give an applicant the default tags if they have none.

    Called lazily on page load rather than only at signup, so applicants that
    predate per-applicant tags get seeded too.
    """
    if applicant is None:
        return
    if EssayCategory.objects.filter(applicant=applicant).exists():
        return
    EssayCategory.objects.bulk_create([
        EssayCategory(applicant=applicant, name=name, sort_order=i)
        for i, name in enumerate(DEFAULT_ESSAY_TAGS)
    ])


class SupplementEssay(models.Model):
    """One essay prompt+response for one college."""
    STATUS_CHOICES = ESSAY_STATUS_CHOICES

    applicant = models.ForeignKey(
        'core.Applicant', null=True, blank=True,
        on_delete=models.CASCADE, related_name='essays'
    )
    college = models.ForeignKey(
        'colleges.UserCollege', on_delete=models.CASCADE,
        related_name='essays'
    )
    category = models.ForeignKey(
        EssayCategory, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='essays'
    )
    prompt = models.TextField(blank=True)
    # Which of the offered prompts this essay answers. Null when the essay has
    # a single prompt (the common case) or when nothing is chosen yet.
    selected_prompt = models.ForeignKey(
        'EssayPrompt', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    # Some prompts give a range ("5-500 words"), most give a ceiling
    # ("max 500"). The minimum is null in the second case.
    word_limit_min = models.IntegerField(null=True, blank=True)
    char_limit_min = models.IntegerField(null=True, blank=True)
    word_limit = models.IntegerField(null=True, blank=True)
    char_limit = models.IntegerField(null=True, blank=True)
    response = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='todo')
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
    def prompt_text(self):
        """The prompt to show: the chosen option, else the plain prompt field.

        Essays imported before EssayPrompt existed keep their text in `prompt`,
        so both are read here rather than migrating one into the other.
        """
        if self.selected_prompt_id:
            return self.selected_prompt.text
        return self.prompt

    @property
    def has_choice(self):
        """True when the college offers a choice of prompts for this essay.

        len() over count() so a prefetched list is reused instead of firing a
        query per essay on the cards.
        """
        return len(self.prompts.all()) > 1


class EssayPrompt(models.Model):
    """One prompt an essay could answer.

    A normal essay has exactly one of these; a "choose one of the following"
    essay has several and one selected. Modelling both the same way means the
    fact that a choice existed survives, instead of being flattened into
    whichever option got pasted in.

    Common App (pick 1 of 7) and the UC PIQs (answer 4 of 8) are the same
    shape, still hardcoded elsewhere; this doesn't preclude folding them in.
    """
    essay = models.ForeignKey(
        SupplementEssay, on_delete=models.CASCADE, related_name='prompts'
    )
    text = models.TextField()
    # Per-option limits: some colleges give different lengths per option. Blank
    # means fall back to the essay's own limit.
    word_limit = models.IntegerField(null=True, blank=True)
    char_limit = models.IntegerField(null=True, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.text[:60]


class UCPersonalInsightQuestion(models.Model):
    STATUS_CHOICES = ESSAY_STATUS_CHOICES

    applicant = models.ForeignKey(
        'core.Applicant', on_delete=models.CASCADE, related_name='uc_piqs'
    )
    question_number = models.IntegerField()  # 1–8
    response = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='todo')

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
    STATUS_CHOICES = ESSAY_STATUS_CHOICES

    applicant = models.OneToOneField(
        'core.Applicant', on_delete=models.CASCADE, related_name='common_app_essay'
    )
    prompt_choice = models.IntegerField(null=True, blank=True)  # 1–7; null = not chosen
    response = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='todo')

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
