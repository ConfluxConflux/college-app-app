from django.db import models


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
