from django.db import models


class UCEntry(models.Model):
    """UC Application activity or award (up to 20)."""
    CATEGORY_CHOICES = [
        ('award', 'Award or honor'),
        ('edu_prep', 'Educational preparation program'),
        ('extracurricular', 'Extracurricular activity'),
        ('volunteer', 'Volunteer / Community Service'),
        ('work', 'Work experience'),
        ('coursework', 'Other coursework'),
    ]

    applicant = models.ForeignKey(
        'core.Applicant', null=True, blank=True,
        on_delete=models.CASCADE, related_name='uc_entries'
    )
    core_activity = models.ForeignKey(
        'core.CoreActivity', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='uc_entries'
    )
    order = models.IntegerField(default=0)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    name = models.CharField(max_length=100)

    # Shared fields (character limits enforced at form layer)
    background = models.CharField(max_length=250, blank=True)
    description = models.CharField(max_length=350, blank=True)

    # Grade levels
    grade_9 = models.BooleanField(default=False)
    grade_10 = models.BooleanField(default=False)
    grade_11 = models.BooleanField(default=False)
    grade_12 = models.BooleanField(default=False)

    # Time commitment
    hours_per_week = models.CharField(max_length=20, blank=True)
    weeks_per_year = models.CharField(max_length=20, blank=True)

    # Award-specific
    recognition_level = models.CharField(max_length=50, blank=True)
    is_academic = models.BooleanField(null=True, blank=True)

    # Work-specific
    earnings_usage = models.CharField(max_length=250, blank=True)
    still_working = models.BooleanField(null=True, blank=True)

    personal_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'UC activity/award'
        verbose_name_plural = 'UC activities & awards'

    def __str__(self):
        return f'{self.name} ({self.get_category_display()})'


class CommonAppActivity(models.Model):
    """Common App activity (up to 10)."""
    ACTIVITY_TYPE_CHOICES = [
        ('academic', 'Academic'),
        ('art', 'Art'),
        ('athletics_club', 'Athletics: Club'),
        ('athletics_jv_varsity', 'Athletics: JV/Varsity'),
        ('career', 'Career Oriented'),
        ('community', 'Community Service (Volunteer)'),
        ('computer_technology', 'Computer/Technology'),
        ('cultural', 'Cultural'),
        ('dance', 'Dance'),
        ('debate_speech', 'Debate/Speech'),
        ('environmental', 'Environmental'),
        ('family_responsibilities', 'Family Responsibilities'),
        ('foreign_exchange', 'Foreign Exchange'),
        ('journalism_publication', 'Journalism/Publication'),
        ('junior_rotc', 'Junior R.O.T.C.'),
        ('lgbtq', 'LGBT'),
        ('music_instrumental', 'Music: Instrumental'),
        ('music_vocal', 'Music: Vocal'),
        ('religious', 'Religious'),
        ('research', 'Research'),
        ('robotics', 'Robotics'),
        ('school_spirit', 'School Spirit'),
        ('science_math', 'Science/Math'),
        ('student_govt', 'Student Govt./Politics'),
        ('theater_drama', 'Theater/Drama'),
        ('work_paid', 'Work (Paid)'),
        ('other', 'Other Club/Activity'),
    ]

    applicant = models.ForeignKey(
        'core.Applicant', null=True, blank=True,
        on_delete=models.CASCADE, related_name='common_app_activities'
    )
    core_activity = models.ForeignKey(
        'core.CoreActivity', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='common_app_activities'
    )
    order = models.IntegerField(default=0)
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPE_CHOICES)
    position = models.CharField(max_length=50, blank=True)
    organization = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=150, blank=True)

    # Grade levels
    grade_9 = models.BooleanField(default=False)
    grade_10 = models.BooleanField(default=False)
    grade_11 = models.BooleanField(default=False)
    grade_12 = models.BooleanField(default=False)

    # Timing
    timing_school = models.BooleanField(default=False)
    timing_breaks = models.BooleanField(default=False)
    timing_all_year = models.BooleanField(default=False)

    # Time commitment
    hours_per_week = models.IntegerField(null=True, blank=True)
    weeks_per_year = models.IntegerField(null=True, blank=True)

    similar_in_college = models.BooleanField(null=True, blank=True)
    personal_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Common App activity'
        verbose_name_plural = 'Common App activities'

    def __str__(self):
        return f'{self.organization} - {self.position}'[:80] or f'Activity #{self.order}'


class CommonAppHonor(models.Model):
    """Common App honor (up to 5)."""
    applicant = models.ForeignKey(
        'core.Applicant', null=True, blank=True,
        on_delete=models.CASCADE, related_name='common_app_honors'
    )
    core_activity = models.ForeignKey(
        'core.CoreActivity', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='common_app_honors'
    )
    order = models.IntegerField(default=0)
    title = models.CharField(max_length=200)

    # Grade levels
    grade_9 = models.BooleanField(default=False)
    grade_10 = models.BooleanField(default=False)
    grade_11 = models.BooleanField(default=False)
    grade_12 = models.BooleanField(default=False)

    # Recognition levels (checkboxes - can select multiple)
    level_school = models.BooleanField(default=False)
    level_state_regional = models.BooleanField(default=False)
    level_national = models.BooleanField(default=False)
    level_international = models.BooleanField(default=False)

    personal_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class MITEntry(models.Model):
    """MIT application entry (jobs, activities, summer activities, distinctions)."""
    CATEGORY_CHOICES = [
        ('job', 'Job'),
        ('activity', 'Activity'),
        ('summer', 'Summer activity'),
        ('scholastic', 'Scholastic distinction'),
        ('non_scholastic', 'Non-scholastic distinction'),
    ]
    CATEGORY_LIMITS = {
        'job': 5,
        'activity': 4,
        'summer': 6,
        'scholastic': 5,
        'non_scholastic': 5,
    }

    applicant = models.ForeignKey(
        'core.Applicant', null=True, blank=True,
        on_delete=models.CASCADE, related_name='mit_entries'
    )
    core_activity = models.ForeignKey(
        'core.CoreActivity', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='mit_entries'
    )
    order = models.IntegerField(default=0)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    org_name = models.CharField(max_length=200, blank=True)
    role_award = models.CharField(max_length=200, blank=True)
    participation_period = models.CharField(max_length=100, blank=True)
    hours_per_week = models.IntegerField(null=True, blank=True)
    weeks_per_year = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)  # 40 word limit enforced at form layer
    personal_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['category', 'order']
        verbose_name = 'MIT entry'
        verbose_name_plural = 'MIT entries'

    def __str__(self):
        return f'{self.org_name} ({self.get_category_display()})'
