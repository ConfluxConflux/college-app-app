from django.db import models


class College(models.Model):
    APPLY_STATUS_CHOICES = [
        ('applying', 'Applying'),
        ('likely', 'Likely'),
        ('considering', 'Considering'),
        ('unlikely', 'Unlikely'),
        ('not_applying', 'Not Applying'),
        ('applied', 'Applied'),
        ('accepted', 'Accepted'),
        ('deferred', 'Deferred'),
        ('waitlisted', 'Waitlisted'),
        ('rejected', 'Rejected'),
        ('enrolled', 'Enrolled'),
    ]

    APP_PLATFORM_CHOICES = [
        ('common', 'Common App'),
        ('uc', 'UC Application'),
        ('mit', 'MIT Application'),
        ('coalition', 'Coalition App'),
        ('georgetown', 'Georgetown'),
        ('ucas', 'UCAS (UK)'),
        ('csu', 'CSU Application'),
        ('canada', 'Canada'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    apply_status = models.CharField(max_length=20, choices=APPLY_STATUS_CHOICES, blank=True)
    tier = models.CharField(max_length=10, blank=True)
    acceptance_rate = models.CharField(max_length=10, blank=True)
    collegevine_chance = models.CharField(max_length=10, blank=True)
    location = models.CharField(max_length=200, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    app_platform = models.CharField(max_length=50, blank=True)
    terms = models.CharField(max_length=50, blank=True)

    # Financial
    cost_of_attendance = models.CharField(max_length=100, blank=True)
    estimated_financial_aid = models.CharField(max_length=100, blank=True)
    estimated_net_cost = models.CharField(max_length=100, blank=True)
    financial_aid_deadline = models.CharField(max_length=20, blank=True)
    fafsa_required = models.BooleanField(null=True, blank=True)
    css_profile_required = models.BooleanField(null=True, blank=True)

    # Academics
    requirements_style = models.CharField(max_length=50, blank=True)
    intended_major = models.CharField(max_length=100, blank=True)
    second_choice_major = models.CharField(max_length=100, blank=True)
    third_choice_major = models.CharField(max_length=100, blank=True)

    # Deadlines
    restrictive_ea = models.CharField(max_length=5, blank=True)
    ea_deadline = models.CharField(max_length=20, blank=True)
    ed1_deadline = models.CharField(max_length=20, blank=True)
    ed2_deadline = models.CharField(max_length=20, blank=True)
    rd_deadline = models.CharField(max_length=20, blank=True)
    other_deadline = models.CharField(max_length=20, blank=True)

    # Application details
    self_report_sat = models.CharField(max_length=20, blank=True)
    interview = models.CharField(max_length=50, blank=True)

    # People
    known_students = models.TextField(blank=True)
    known_faculty = models.TextField(blank=True)

    # Logistics
    toured = models.CharField(max_length=20, blank=True)
    portal_info = models.TextField(blank=True)

    # Notes
    applicant_notes = models.TextField(blank=True)
    parent_notes = models.TextField(blank=True)
    random_notes = models.TextField(blank=True)

    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def status_color(self):
        """Return a CSS class for conditional formatting by apply status."""
        return {
            'applying': 'is-success',
            'likely': 'is-info',
            'considering': 'is-warning',
            'unlikely': 'is-danger-light',
            'not_applying': 'is-light',
            'applied': 'is-link',
            'accepted': 'is-success',
            'deferred': 'is-warning',
            'waitlisted': 'is-warning',
            'rejected': 'is-danger',
            'enrolled': 'is-primary',
        }.get(self.apply_status, '')
