from django.db import models


class Applicant(models.Model):
    """Represents one applicant (future: linked to a real auth user).
    All application data — colleges, activities, essays — belongs to an Applicant."""
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    # Static file path (e.g. 'img/profile.jpeg') or external URL
    profile_picture = models.CharField(max_length=300, blank=True, default='img/default_profile.png')
    brainstorm = models.TextField(blank=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class CoreActivity(models.Model):
    """The 'hub' representing a real-world activity, job, or honor.
    Format-specific entries (UC, Common App, MIT) link back here.
    This lets users see one activity across all application formats."""
    applicant = models.ForeignKey(
        Applicant, null=True, blank=True,
        on_delete=models.CASCADE, related_name='core_activities'
    )
    name = models.CharField(max_length=300)
    full_description = models.TextField(blank=True)
    personal_notes = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    # Shared data — fill these in the Centralized tab
    grade_9 = models.BooleanField(default=False)
    grade_10 = models.BooleanField(default=False)
    grade_11 = models.BooleanField(default=False)
    grade_12 = models.BooleanField(default=False)
    hours_per_week = models.CharField(max_length=20, blank=True)
    weeks_per_year = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'core activities'

    def __str__(self):
        return self.name
