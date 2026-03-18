from django.db import models


class CoreActivity(models.Model):
    """The 'hub' representing a real-world activity, job, or honor.
    Format-specific entries (UC, Common App, MIT) link back here.
    This lets users see one activity across all application formats."""
    name = models.CharField(max_length=300)
    full_description = models.TextField(blank=True)
    personal_notes = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'core activities'

    def __str__(self):
        return self.name
