from django.db import models


APPLY_STATUS_CHOICES = [
    ('applying', 'Applying'),
    ('likely', 'Likely'),
    ('considering', 'Considering'),
    ('unlikely', 'Unlikely'),
    ('not_applying', 'Not Applying'),
    ('applied', 'Submitted'),
    ('accepted', 'Accepted'),
    ('deferred', 'Deferred'),
    ('waitlisted', 'Waitlisted'),
    ('rejected', 'Rejected'),
    ('enrolled', 'Enrolled'),
    ('withdrawn', 'Withdrawn'),
]

DIFFICULTY_CHOICES = [
    ('safety', 'Safety'),
    ('target', 'Target'),
    ('reach', 'Reach'),
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


class College(models.Model):
    """Canonical college data, shared across all users. Populated from IPEDS and other sources."""

    # Immutable identity
    unitid = models.CharField(max_length=20, unique=True, blank=True, null=True)
    name = models.CharField(max_length=200)

    # Canonical location
    city = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    # Canonical academic/financial (from IPEDS)
    tuition_instate = models.IntegerField(null=True, blank=True)
    fees_instate = models.IntegerField(null=True, blank=True)
    tuition_outofstate = models.IntegerField(null=True, blank=True)
    fees_outofstate = models.IntegerField(null=True, blank=True)
    room = models.IntegerField(null=True, blank=True)
    board = models.IntegerField(null=True, blank=True)
    total_cost = models.IntegerField(null=True, blank=True)
    avg_grant_aid = models.IntegerField(null=True, blank=True)
    academic_calendar = models.CharField(max_length=50, blank=True)
    acceptance_rate = models.CharField(max_length=20, blank=True)
    sat_avg = models.IntegerField(null=True, blank=True)
    undergrad_enrollment = models.IntegerField(null=True, blank=True)
    app_platform = models.CharField(max_length=50, blank=True)
    fafsa_required = models.BooleanField(null=True, blank=True)
    css_profile_required = models.BooleanField(null=True, blank=True)
    proof_acceptances = models.IntegerField(default=0)

    # Future canonical (blank for now; will be populated from official sources)
    restrictive_ea = models.CharField(max_length=5, blank=True)
    ea_deadline = models.CharField(max_length=20, blank=True)
    ed1_deadline = models.CharField(max_length=20, blank=True)
    ed2_deadline = models.CharField(max_length=20, blank=True)
    rd_deadline = models.CharField(max_length=20, blank=True)
    other_deadline = models.CharField(max_length=20, blank=True)
    financial_aid_deadline = models.CharField(max_length=20, blank=True)
    cost_of_attendance = models.CharField(max_length=100, blank=True)
    interview = models.CharField(max_length=50, blank=True)
    self_report_sat = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class UserCollege(models.Model):
    """Per-user college tracking: application status, notes, and optional overrides of canonical data."""

    # Expose choices as class attributes for template/view compatibility
    APPLY_STATUS_CHOICES = APPLY_STATUS_CHOICES
    DIFFICULTY_CHOICES = DIFFICULTY_CHOICES
    APP_PLATFORM_CHOICES = APP_PLATFORM_CHOICES

    applicant = models.ForeignKey(
        'core.Applicant', null=True, blank=True,
        on_delete=models.CASCADE, related_name='colleges'
    )
    college = models.ForeignKey(
        College, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='user_colleges'
    )
    display_name = models.CharField(max_length=200, blank=True)

    # Pure per-user fields
    apply_status = models.CharField(max_length=20, choices=APPLY_STATUS_CHOICES, default='not_applying')
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, blank=True)
    tier = models.CharField(max_length=10, blank=True)
    collegevine_chance = models.CharField(max_length=10, blank=True)
    location = models.CharField(max_length=200, blank=True)  # narrative description
    requirements_style = models.CharField(max_length=50, blank=True)
    intended_major = models.CharField(max_length=100, blank=True)
    second_choice_major = models.CharField(max_length=100, blank=True)
    third_choice_major = models.CharField(max_length=100, blank=True)
    estimated_financial_aid = models.CharField(max_length=100, blank=True)
    estimated_net_cost = models.CharField(max_length=100, blank=True)
    known_students = models.TextField(blank=True)
    known_faculty = models.TextField(blank=True)
    toured = models.CharField(max_length=20, blank=True)
    portal_info = models.TextField(blank=True)
    applicant_notes = models.TextField(blank=True)
    parent_notes = models.TextField(blank=True)
    random_notes = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    # Override fields — when set, shadow the canonical College value
    city_override = models.CharField(max_length=200, blank=True)
    state_override = models.CharField(max_length=10, blank=True)
    country_override = models.CharField(max_length=100, blank=True)
    latitude_override = models.FloatField(null=True, blank=True)
    longitude_override = models.FloatField(null=True, blank=True)
    tuition_instate_override = models.IntegerField(null=True, blank=True)
    fees_instate_override = models.IntegerField(null=True, blank=True)
    tuition_outofstate_override = models.IntegerField(null=True, blank=True)
    fees_outofstate_override = models.IntegerField(null=True, blank=True)
    room_override = models.IntegerField(null=True, blank=True)
    board_override = models.IntegerField(null=True, blank=True)
    total_cost_override = models.IntegerField(null=True, blank=True)
    avg_grant_aid_override = models.IntegerField(null=True, blank=True)
    academic_calendar_override = models.CharField(max_length=50, blank=True)
    acceptance_rate_override = models.CharField(max_length=20, blank=True)
    sat_avg_override = models.IntegerField(null=True, blank=True)
    undergrad_enrollment_override = models.IntegerField(null=True, blank=True)
    app_platform_override = models.CharField(max_length=50, blank=True)
    fafsa_required_override = models.BooleanField(null=True, blank=True)
    css_profile_required_override = models.BooleanField(null=True, blank=True)
    restrictive_ea_override = models.CharField(max_length=5, blank=True)
    ea_deadline_override = models.CharField(max_length=20, blank=True)
    ed1_deadline_override = models.CharField(max_length=20, blank=True)
    ed2_deadline_override = models.CharField(max_length=20, blank=True)
    rd_deadline_override = models.CharField(max_length=20, blank=True)
    other_deadline_override = models.CharField(max_length=20, blank=True)
    financial_aid_deadline_override = models.CharField(max_length=20, blank=True)
    cost_of_attendance_override = models.CharField(max_length=100, blank=True)
    interview_override = models.CharField(max_length=50, blank=True)
    self_report_sat_override = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['order', 'college__name']

    def __str__(self):
        return self.name

    # ------------------------------------------------------------------ #
    # effective() — canonical fallback logic                               #
    # ------------------------------------------------------------------ #

    def _effective_str(self, field):
        """Return override if non-empty, else canonical value (for string fields)."""
        v = getattr(self, f'{field}_override', None)
        if v:
            return v
        return getattr(self.college, field, '') if self.college else ''

    def _effective_nullable(self, field):
        """Return override if not None, else canonical value (for int/float/bool fields)."""
        v = getattr(self, f'{field}_override', None)
        if v is not None:
            return v
        return getattr(self.college, field, None) if self.college else None

    # ------------------------------------------------------------------ #
    # Properties with getters + setters for all canonical/future-canonical #
    # fields — allows templates and views to use the original field names   #
    # ------------------------------------------------------------------ #

    @property
    def name(self):
        return self.display_name or (self.college.name if self.college else '')

    @name.setter
    def name(self, value):
        self.display_name = value

    @property
    def city(self):
        return self._effective_str('city')

    @city.setter
    def city(self, value):
        self.city_override = value

    @property
    def state(self):
        return self._effective_str('state')

    @state.setter
    def state(self, value):
        self.state_override = value

    @property
    def country(self):
        return self._effective_str('country')

    @country.setter
    def country(self, value):
        self.country_override = value

    @property
    def latitude(self):
        return self._effective_nullable('latitude')

    @latitude.setter
    def latitude(self, value):
        self.latitude_override = value

    @property
    def longitude(self):
        return self._effective_nullable('longitude')

    @longitude.setter
    def longitude(self, value):
        self.longitude_override = value

    @property
    def acceptance_rate(self):
        return self._effective_str('acceptance_rate')

    @acceptance_rate.setter
    def acceptance_rate(self, value):
        self.acceptance_rate_override = value

    @property
    def sat_avg(self):
        return self._effective_nullable('sat_avg')

    @sat_avg.setter
    def sat_avg(self, value):
        self.sat_avg_override = value

    @property
    def undergrad_enrollment(self):
        return self._effective_nullable('undergrad_enrollment')

    @undergrad_enrollment.setter
    def undergrad_enrollment(self, value):
        self.undergrad_enrollment_override = value

    @property
    def app_platform(self):
        return self._effective_str('app_platform')

    @app_platform.setter
    def app_platform(self, value):
        self.app_platform_override = value

    @property
    def terms(self):
        """'terms' is the legacy name; canonical field is academic_calendar."""
        return self._effective_str('academic_calendar')

    @terms.setter
    def terms(self, value):
        self.academic_calendar_override = value

    @property
    def fafsa_required(self):
        return self._effective_nullable('fafsa_required')

    @fafsa_required.setter
    def fafsa_required(self, value):
        self.fafsa_required_override = value

    @property
    def css_profile_required(self):
        return self._effective_nullable('css_profile_required')

    @css_profile_required.setter
    def css_profile_required(self, value):
        self.css_profile_required_override = value

    @property
    def restrictive_ea(self):
        return self._effective_str('restrictive_ea')

    @restrictive_ea.setter
    def restrictive_ea(self, value):
        self.restrictive_ea_override = value

    @property
    def ea_deadline(self):
        return self._effective_str('ea_deadline')

    @ea_deadline.setter
    def ea_deadline(self, value):
        self.ea_deadline_override = value

    @property
    def ed1_deadline(self):
        return self._effective_str('ed1_deadline')

    @ed1_deadline.setter
    def ed1_deadline(self, value):
        self.ed1_deadline_override = value

    @property
    def ed2_deadline(self):
        return self._effective_str('ed2_deadline')

    @ed2_deadline.setter
    def ed2_deadline(self, value):
        self.ed2_deadline_override = value

    @property
    def rd_deadline(self):
        return self._effective_str('rd_deadline')

    @rd_deadline.setter
    def rd_deadline(self, value):
        self.rd_deadline_override = value

    @property
    def other_deadline(self):
        return self._effective_str('other_deadline')

    @other_deadline.setter
    def other_deadline(self, value):
        self.other_deadline_override = value

    @property
    def financial_aid_deadline(self):
        return self._effective_str('financial_aid_deadline')

    @financial_aid_deadline.setter
    def financial_aid_deadline(self, value):
        self.financial_aid_deadline_override = value

    @property
    def cost_of_attendance(self):
        return self._effective_str('cost_of_attendance')

    @cost_of_attendance.setter
    def cost_of_attendance(self, value):
        self.cost_of_attendance_override = value

    @property
    def interview(self):
        return self._effective_str('interview')

    @interview.setter
    def interview(self, value):
        self.interview_override = value

    @property
    def self_report_sat(self):
        return self._effective_str('self_report_sat')

    @self_report_sat.setter
    def self_report_sat(self, value):
        self.self_report_sat_override = value

    @property
    def tuition_instate(self):
        return self._effective_nullable('tuition_instate')

    @tuition_instate.setter
    def tuition_instate(self, value):
        self.tuition_instate_override = value

    @property
    def tuition_outofstate(self):
        return self._effective_nullable('tuition_outofstate')

    @tuition_outofstate.setter
    def tuition_outofstate(self, value):
        self.tuition_outofstate_override = value

    @property
    def fees_instate(self):
        return self._effective_nullable('fees_instate')

    @fees_instate.setter
    def fees_instate(self, value):
        self.fees_instate_override = value

    @property
    def fees_outofstate(self):
        return self._effective_nullable('fees_outofstate')

    @fees_outofstate.setter
    def fees_outofstate(self, value):
        self.fees_outofstate_override = value

    @property
    def room(self):
        return self._effective_nullable('room')

    @room.setter
    def room(self, value):
        self.room_override = value

    @property
    def board(self):
        return self._effective_nullable('board')

    @board.setter
    def board(self, value):
        self.board_override = value

    @property
    def total_cost(self):
        return self._effective_nullable('total_cost')

    @total_cost.setter
    def total_cost(self, value):
        self.total_cost_override = value

    @property
    def avg_grant_aid(self):
        return self._effective_nullable('avg_grant_aid')

    @avg_grant_aid.setter
    def avg_grant_aid(self, value):
        self.avg_grant_aid_override = value

    # ------------------------------------------------------------------ #
    # Display helpers                                                       #
    # ------------------------------------------------------------------ #

    @property
    def difficulty_color(self):
        return {
            'safety': 'background:#bbf7d0;color:#14532d;',
            'target': 'background:#bfdbfe;color:#1e3a8a;',
            'reach': 'background:#e9d5ff;color:#581c87;',
        }.get(self.difficulty, '')

    @property
    def status_color(self):
        return {
            'applying': 'pill-applying',
            'likely': 'is-info',
            'considering': 'pill-considering',
            'unlikely': 'is-danger-light',
            'not_applying': 'is-light',
            'applied': 'is-link',
            'accepted': 'is-success',
            'deferred': 'is-warning',
            'waitlisted': 'is-warning',
            'rejected': 'is-danger',
            'enrolled': 'is-primary',
        }.get(self.apply_status, '')
