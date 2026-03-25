import json
from collections import defaultdict

from django.db.models import Case, When, Value, IntegerField
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods

from .forms import CollegeForm
from .models import College
from activities.models import UCEntry, CommonAppActivity, CommonAppHonor, MITEntry
from core.models import Applicant
from core.utils import get_applicant
from supplements.models import SupplementEssay, UCPersonalInsightQuestion, CommonAppEssay, UC_PIQ_PROMPTS, COMMON_APP_PROMPTS


# Always-visible columns
DEFAULT_FIELDS = [
    ('name', 'College'),
    ('apply_status', 'Status'),
    ('applicant_notes', 'Notes'),
]

# Optional columns the user can toggle on
OPTIONAL_FIELDS = [
    ('tier', 'Tier'),
    ('difficulty', 'Difficulty'),
    ('acceptance_rate', 'Acc. Rate'),
    ('collegevine_chance', 'CV Chance'),
    ('sat_avg', 'SAT Avg'),
    ('undergrad_enrollment', 'Enrollment'),
    ('location', 'Location'),
    ('app_platform', 'Platform'),
    ('terms', 'Terms'),
    ('ea_deadline', 'EA'),
    ('ed1_deadline', 'ED I'),
    ('ed2_deadline', 'ED II'),
    ('rd_deadline', 'RD'),
    ('intended_major', 'Major'),
    ('parent_notes', 'Parent Notes'),
]

ALL_TABLE_FIELDS = DEFAULT_FIELDS + OPTIONAL_FIELDS
ALL_TABLE_FIELDS_DICT = dict(ALL_TABLE_FIELDS)
EDITABLE_FIELDS = {f[0] for f in ALL_TABLE_FIELDS}

# The three views and which statuses they show
VIEWS = {
    'applications': {
        'label': 'Your Applications',
        'statuses': ['applying', 'likely', 'considering', 'unlikely'],  # likely/unlikely kept for legacy data
    },
    'all': {
        'label': 'All Colleges',
        'statuses': None,  # no filter
    },
    'submitted': {
        'label': 'Submitted',
        'statuses': ['applied', 'deferred', 'waitlisted', 'rejected', 'enrolled', 'withdrawn'],
    },
}

# Sort order for Applications page
APP_PROGRESS_STATUS_ORDER = Case(
    When(apply_status='applying', then=Value(1)),
    When(apply_status='likely', then=Value(2)),
    When(apply_status='considering', then=Value(3)),
    When(apply_status='unlikely', then=Value(4)),
    When(apply_status='deferred', then=Value(5)),
    When(apply_status='waitlisted', then=Value(6)),
    When(apply_status='applied', then=Value(7)),
    When(apply_status='accepted', then=Value(8)),
    When(apply_status='rejected', then=Value(9)),
    When(apply_status='enrolled', then=Value(10)),
    When(apply_status='not_applying', then=Value(11)),
    When(apply_status='withdrawn', then=Value(12)),
    default=Value(13),
    output_field=IntegerField(),
)

# Sort order for "All Colleges" view
STATUS_ORDER = Case(
    When(apply_status='not_applying', then=Value(1)),
    When(apply_status='considering', then=Value(2)),
    When(apply_status='unlikely', then=Value(3)),
    When(apply_status='applying', then=Value(4)),
    When(apply_status='likely', then=Value(5)),
    When(apply_status='applied', then=Value(6)),
    When(apply_status='deferred', then=Value(7)),
    When(apply_status='waitlisted', then=Value(8)),
    When(apply_status='rejected', then=Value(9)),
    When(apply_status='accepted', then=Value(10)),
    When(apply_status='enrolled', then=Value(11)),
    When(apply_status='withdrawn', then=Value(12)),
    default=Value(13),
    output_field=IntegerField(),
)


def college_list(request):
    current_view = request.GET.get('view', 'applications')
    if current_view not in VIEWS:
        current_view = 'applications'

    applicant = get_applicant(request)
    view_config = VIEWS[current_view]
    colleges = College.objects.filter(applicant=applicant)

    # Apply view filter
    if view_config['statuses']:
        colleges = colleges.filter(apply_status__in=view_config['statuses'])

    # Sorting — "all" defaults to likelihood order; others default to model ordering
    sort = request.GET.get('sort', '')
    sort_dir = request.GET.get('dir', 'asc')
    if sort in EDITABLE_FIELDS:
        order = sort if sort_dir == 'asc' else f'-{sort}'
        colleges = colleges.order_by(order)
    elif current_view == 'all':
        colleges = colleges.annotate(status_order=STATUS_ORDER).order_by('status_order', 'name')

    # Search
    search = request.GET.get('q', '')
    if search:
        colleges = colleges.filter(name__icontains=search)

    # Status sub-filter (within the current view's statuses)
    status_filter = request.GET.get('status', '')
    if status_filter:
        colleges = colleges.filter(apply_status=status_filter)

    platform_tracker = _build_platform_tracker(applicant)

    # Status choices for the filter dropdown — limit to current view's statuses, exclude hidden statuses
    HIDDEN_STATUSES = {'likely', 'unlikely'}
    all_choices = dict(College.APPLY_STATUS_CHOICES)
    if view_config['statuses']:
        view_status_choices = [(v, all_choices[v]) for v in view_config['statuses'] if v in all_choices and v not in HIDDEN_STATUSES]
    else:
        view_status_choices = [(v, l) for v, l in College.APPLY_STATUS_CHOICES if v not in HIDDEN_STATUSES]

    context = {
        'colleges': colleges,
        'table_fields': ALL_TABLE_FIELDS,
        'optional_fields': OPTIONAL_FIELDS,
        'optional_field_names': {f[0] for f in OPTIONAL_FIELDS},
        'sort': sort,
        'sort_dir': sort_dir,
        'status_filter': status_filter,
        'search': search,
        'status_choices': view_status_choices,
        'current_view': current_view,
        'views': VIEWS,
        'platform_tracker': platform_tracker,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'colleges/_college_table.html', context)

    return render(request, 'colleges/college_list.html', context)


def _build_platform_tracker(applicant):
    APPLYING_STATUSES = {'applying', 'applied', 'deferred', 'waitlisted', 'accepted', 'enrolled'}
    CONSIDERING_STATUSES = {'considering'}
    applying_platforms = set(
        College.objects.filter(applicant=applicant, apply_status__in=APPLYING_STATUSES)
        .values_list('app_platform', flat=True)
    )
    considering_platforms = set(
        College.objects.filter(applicant=applicant, apply_status__in=CONSIDERING_STATUSES)
        .values_list('app_platform', flat=True)
    )
    def _state(keyword):
        if any(keyword.lower() in (p or '').lower() for p in applying_platforms):
            return 'applying'
        if any(keyword.lower() in (p or '').lower() for p in considering_platforms):
            return 'considering'
        return 'none'
    mit = College.objects.filter(applicant=applicant, app_platform__iexact='mit').first()
    return [
        {'label': 'Common App', 'state': _state('common'),     'supported': True,  'href': '/applications/common/'},
        {'label': 'UC App',     'state': _state('uc'),         'supported': True,  'href': '/applications/uc/'},
        {'label': 'MIT App',    'state': _state('mit'),        'supported': True,  'href': f'/applications/?college={mit.pk}' if mit else None},
        {'label': 'CSU App',    'state': _state('csu'),        'supported': False, 'href': None},
        {'label': 'UCAS',       'state': _state('ucas'),       'supported': False, 'href': None},
        {'label': 'Canadian',   'state': _state('canada'),     'supported': False, 'href': None},
        {'label': 'Georgetown', 'state': _state('georgetown'), 'supported': False, 'href': None},
        {'label': 'Minerva',    'state': _state('minerva'),    'supported': False, 'href': None},
    ]


def college_detail(request, pk):
    college = get_object_or_404(College, pk=pk)
    if request.method == 'POST':
        form = CollegeForm(request.POST, instance=college)
        if form.is_valid():
            form.save()
            if request.headers.get('HX-Request'):
                return render(request, 'colleges/_college_row.html', {
                    'college': college, 'table_fields': ALL_TABLE_FIELDS
                })
            return redirect('colleges:list')
    else:
        form = CollegeForm(instance=college)

    return render(request, 'colleges/college_detail.html', {
        'college': college, 'form': form
    })


def college_edit_cell(request, pk, field):
    """Inline cell editing via htmx."""
    college = get_object_or_404(College, pk=pk)

    if field not in EDITABLE_FIELDS:
        return HttpResponse('Invalid field', status=400)

    if request.method == 'POST':
        value = request.POST.get('value', '')
        setattr(college, field, value)
        college.save()
        ctx = {'college': college, 'table_fields': ALL_TABLE_FIELDS, 'optional_field_names': {f[0] for f in OPTIONAL_FIELDS}}
        if field == 'apply_status':
            applicant = get_applicant(request)
            ctx['platform_tracker'] = _build_platform_tracker(applicant)
            return render(request, 'colleges/_college_row_with_tracker.html', ctx)
        return render(request, 'colleges/_college_row.html', ctx)

    current_value = getattr(college, field, '')
    field_label = ALL_TABLE_FIELDS_DICT.get(field, field)

    if field == 'apply_status':
        hidden = {'likely', 'unlikely'}
        choices = [(v, l) for v, l in College.APPLY_STATUS_CHOICES if v not in hidden]
        return render(request, 'colleges/_cell_edit_select.html', {
            'college': college, 'field': field, 'field_label': field_label,
            'current_value': current_value, 'choices': choices,
            'table_fields': ALL_TABLE_FIELDS,
        })

    if field == 'difficulty':
        return render(request, 'colleges/_cell_edit_select.html', {
            'college': college, 'field': field, 'field_label': field_label,
            'current_value': current_value, 'choices': College.DIFFICULTY_CHOICES,
            'table_fields': ALL_TABLE_FIELDS,
        })

    return render(request, 'colleges/_cell_edit.html', {
        'college': college, 'field': field, 'field_label': field_label,
        'current_value': current_value, 'table_fields': ALL_TABLE_FIELDS,
    })


@require_POST
def college_add_row(request):
    applicant = get_applicant(request)
    college = College.objects.create(
        applicant=applicant,
        name='',
        apply_status='applying',
        order=College.objects.filter(applicant=applicant).count(),
    )
    return render(request, 'colleges/_cell_edit.html', {
        'college': college,
        'field': 'name',
        'field_label': 'College',
        'current_value': '',
        'table_fields': ALL_TABLE_FIELDS,
    })


def college_add(request):
    if request.method == 'POST':
        form = CollegeForm(request.POST)
        if form.is_valid():
            college = form.save(commit=False)
            college.applicant = get_applicant(request)
            college.order = College.objects.filter(applicant=college.applicant).count()
            college.save()
            return redirect('colleges:list')
    else:
        form = CollegeForm(initial={'apply_status': 'not_applying'})

    return render(request, 'colleges/college_add.html', {'form': form})


def college_json(request):
    """JSON endpoint for Tabulator data loading."""
    current_view = request.GET.get('view', 'applications')
    if current_view not in VIEWS:
        current_view = 'applications'

    applicant = get_applicant(request)
    view_config = VIEWS[current_view]
    colleges = College.objects.filter(applicant=applicant)

    if view_config['statuses']:
        colleges = colleges.filter(apply_status__in=view_config['statuses'])

    search = request.GET.get('q', '')
    if search:
        colleges = colleges.filter(name__icontains=search)

    if current_view == 'all':
        colleges = colleges.annotate(status_order=STATUS_ORDER).order_by('status_order', 'name')

    status_display = dict(College.APPLY_STATUS_CHOICES)
    data = []
    for c in colleges:
        data.append({
            'id': c.pk,
            'name': c.name,
            'apply_status': c.apply_status,
            'apply_status_display': status_display.get(c.apply_status, c.apply_status),
            'applicant_notes': c.applicant_notes,
            'tier': c.tier,
            'acceptance_rate': c.acceptance_rate,
            'collegevine_chance': c.collegevine_chance,
            'sat_avg': c.sat_avg if c.sat_avg is not None else '',
            'undergrad_enrollment': c.undergrad_enrollment if c.undergrad_enrollment is not None else '',
            'location': c.location,
            'app_platform': c.app_platform,
            'terms': c.terms,
            'ea_deadline': c.ea_deadline,
            'ed1_deadline': c.ed1_deadline,
            'ed2_deadline': c.ed2_deadline,
            'rd_deadline': c.rd_deadline,
            'intended_major': c.intended_major,
            'parent_notes': c.parent_notes,
        })

    return JsonResponse(data, safe=False)


@require_http_methods(['POST'])
def college_update(request, pk):
    """Save a single field edit from Tabulator's cellEdited callback."""
    college = get_object_or_404(College, pk=pk)
    try:
        body = json.loads(request.body)
        field = body.get('field')
        value = body.get('value', '')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if field not in EDITABLE_FIELDS:
        return JsonResponse({'error': 'Invalid field'}, status=400)

    setattr(college, field, value)
    college.save()
    return JsonResponse({'ok': True})


@require_POST
def college_delete(request, pk):
    college = get_object_or_404(College, pk=pk)
    college.delete()
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    return redirect('colleges:list')


APP_STATUS_ORDER_MAP = {
    'applying': 1, 'likely': 2, 'considering': 3, 'unlikely': 4,
    'deferred': 5, 'waitlisted': 6, 'applied': 7, 'accepted': 8,
    'rejected': 9, 'enrolled': 10, 'not_applying': 11, 'withdrawn': 12,
}


class SpecialAppEntry:
    """Synthetic dropdown entry for Common App / UC App."""
    def __init__(self, pk, name):
        self.pk = pk
        self.name = name


def _build_dropdown_colleges(applicant):
    """Returns ordered list for the Applications dropdown, with Common App and UC App
    inserted at the top of their respective status category."""
    colleges = list(
        College.objects.filter(applicant=applicant)
        .annotate(status_order=APP_PROGRESS_STATUS_ORDER)
        .order_by('status_order', 'name')
    )

    APPLYING_STATUSES = {'applying', 'applied', 'deferred', 'waitlisted', 'accepted', 'enrolled'}
    CONSIDERING_STATUSES = {'considering'}
    applying_platforms = set(
        College.objects.filter(applicant=applicant, apply_status__in=APPLYING_STATUSES)
        .values_list('app_platform', flat=True)
    )
    considering_platforms = set(
        College.objects.filter(applicant=applicant, apply_status__in=CONSIDERING_STATUSES)
        .values_list('app_platform', flat=True)
    )

    def _state(keyword):
        if any(keyword.lower() in (p or '').lower() for p in applying_platforms):
            return 'applying'
        if any(keyword.lower() in (p or '').lower() for p in considering_platforms):
            return 'considering'
        return 'none'

    common_order = APP_STATUS_ORDER_MAP.get(_state('common'), 13)
    uc_order = APP_STATUS_ORDER_MAP.get(_state('uc'), 13)

    result = []
    common_inserted = False
    uc_inserted = False

    for college in colleges:
        col_order = APP_STATUS_ORDER_MAP.get(college.apply_status, 13)
        if not common_inserted and common_order <= col_order:
            result.append(SpecialAppEntry('__common__', 'Common App'))
            common_inserted = True
        if not uc_inserted and uc_order <= col_order:
            result.append(SpecialAppEntry('__uc__', 'UC App'))
            uc_inserted = True
        result.append(college)

    if not common_inserted:
        result.append(SpecialAppEntry('__common__', 'Common App'))
    if not uc_inserted:
        result.append(SpecialAppEntry('__uc__', 'UC App'))

    return result


def applications(request):
    applicant = get_applicant(request)
    colleges = _build_dropdown_colleges(applicant)

    selected = None
    selected_pk = request.GET.get('college')
    if selected_pk:
        try:
            pk_int = int(selected_pk)
            selected = College.objects.filter(applicant=applicant, pk=pk_int).first()
        except (ValueError, TypeError):
            pass

    # Status choices for the status badge dropdown
    status_choices = [
        ('applying', 'Applying'),
        ('considering', 'Considering'),
        ('not_applying', 'Not Applying'),
        ('applied', 'Submitted'),
        ('deferred', 'Deferred'),
        ('waitlisted', 'Waitlisted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('enrolled', 'Enrolled'),
        ('withdrawn', 'Withdrawn'),
    ]

    # Per-college dashboard data (only computed when a college is selected)
    essays = []
    essay_done = essay_wip = essay_maybe = essay_blank = essay_total = 0
    essay_done_pct = essay_wip_pct = 0

    platform = ''
    platform_display = ''
    activities_tab = 'uc'
    ca_activities = []
    ca_honors = []
    ca_count = honor_count = 0
    uc_entries = []
    uc_count = 0
    mit_entries_grouped = []
    mit_count = 0
    act_filled = act_max = 0

    if selected:
        # Essays for this college
        essays = list(
            SupplementEssay.objects.filter(college=selected)
            .select_related('category')
            .order_by('sort_order')
        )
        essay_total = len(essays)
        essay_done = sum(1 for e in essays if e.status == 'done')
        essay_wip = sum(1 for e in essays if e.status == 'wip')
        essay_maybe = sum(1 for e in essays if e.status == 'maybe')
        essay_blank = essay_total - essay_done - essay_wip - essay_maybe

        if essay_total > 0:
            essay_done_pct = int(essay_done / essay_total * 100)
            essay_wip_pct = int(essay_wip / essay_total * 100)

        # Augment each essay with computed display fields
        for essay in essays:
            if essay.word_limit and essay.word_limit > 0:
                essay.progress_pct = min(int(essay.word_count / essay.word_limit * 100), 100)
                essay.limit_display = f"{essay.word_limit}w"
                essay.count_display = f"{essay.word_count}/{essay.word_limit}"
            elif essay.char_limit and essay.char_limit > 0:
                essay.progress_pct = min(int(essay.char_count / essay.char_limit * 100), 100)
                essay.limit_display = f"{essay.char_limit}ch"
                essay.count_display = f"{essay.char_count}/{essay.char_limit}"
            else:
                essay.progress_pct = 0
                essay.limit_display = ""
                essay.count_display = str(essay.word_count) if essay.response else ""

        # Platform-aware activities data
        platform = selected.app_platform
        platform_display = dict(College.APP_PLATFORM_CHOICES).get(platform, '') if platform else ''

        try:
            applicant = get_applicant(request)
        except Applicant.DoesNotExist:
            applicant = None

        if applicant:
            if platform == 'common':
                ca_activities = list(
                    CommonAppActivity.objects.filter(applicant=applicant).order_by('order')
                )
                ca_honors = list(
                    CommonAppHonor.objects.filter(applicant=applicant).order_by('order')
                )
                ca_count = len(ca_activities)
                honor_count = len(ca_honors)
                act_filled = ca_count + honor_count
                act_max = 15
                activities_tab = 'common'
            elif platform == 'uc':
                uc_entries = list(
                    UCEntry.objects.filter(applicant=applicant).order_by('order')
                )
                uc_count = len(uc_entries)
                act_filled = uc_count
                act_max = 20
                activities_tab = 'uc'
            elif platform == 'mit':
                mit_qs = list(MITEntry.objects.filter(applicant=applicant).order_by('order'))
                mit_count = len(mit_qs)
                cat_map = defaultdict(list)
                for entry in mit_qs:
                    cat_map[entry.category].append(entry)
                cat_labels = dict(MITEntry.CATEGORY_CHOICES)
                mit_entries_grouped = [
                    {
                        'category': cat,
                        'label': cat_labels.get(cat, cat),
                        'limit': MITEntry.CATEGORY_LIMITS.get(cat, 0),
                        'entries': cat_map[cat],
                        'count': len(cat_map[cat]),
                    }
                    for cat, _ in MITEntry.CATEGORY_CHOICES
                ]
                act_filled = mit_count
                act_max = sum(MITEntry.CATEGORY_LIMITS.values())
                activities_tab = 'mit'

    return render(request, 'colleges/applications.html', {
        'colleges': colleges,
        'selected': selected,
        'status_choices': status_choices,
        # essays
        'essays': essays,
        'essay_status_choices': SupplementEssay.STATUS_CHOICES,
        'essay_done': essay_done,
        'essay_wip': essay_wip,
        'essay_maybe': essay_maybe,
        'essay_blank': essay_blank,
        'essay_total': essay_total,
        'essay_done_pct': essay_done_pct,
        'essay_wip_pct': essay_wip_pct,
        # activities
        'platform': platform,
        'platform_display': platform_display,
        'activities_tab': activities_tab,
        'ca_activities': ca_activities,
        'ca_honors': ca_honors,
        'ca_count': ca_count,
        'honor_count': honor_count,
        'uc_entries': uc_entries,
        'uc_count': uc_count,
        'mit_entries_grouped': mit_entries_grouped,
        'mit_count': mit_count,
        'act_filled': act_filled,
        'act_max': act_max,
    })


def applications_uc(request):
    applicant = get_applicant(request)
    colleges = _build_dropdown_colleges(applicant)

    # UC activities
    uc_entries = list(UCEntry.objects.filter(applicant=applicant).order_by('order'))
    uc_count = len(uc_entries)

    # Ensure all 8 PIQs exist for this applicant
    existing = {piq.question_number for piq in UCPersonalInsightQuestion.objects.filter(applicant=applicant)}
    for n in range(1, 9):
        if n not in existing:
            UCPersonalInsightQuestion.objects.create(applicant=applicant, question_number=n)
    piqs = list(UCPersonalInsightQuestion.objects.filter(applicant=applicant).order_by('question_number'))

    piq_done = sum(1 for p in piqs if p.status == 'done')
    piq_wip = sum(1 for p in piqs if p.status == 'wip')
    piq_maybe = sum(1 for p in piqs if p.status == 'maybe')

    return render(request, 'colleges/applications_uc.html', {
        'colleges': colleges,
        'uc_entries': uc_entries,
        'uc_count': uc_count,
        'piqs': piqs,
        'piq_done': piq_done,
        'piq_wip': piq_wip,
        'piq_maybe': piq_maybe,
        'status_choices': UCPersonalInsightQuestion.STATUS_CHOICES,
    })


def applications_common(request):
    applicant = get_applicant(request)
    colleges = _build_dropdown_colleges(applicant)

    # Common App activities + honors
    ca_activities = list(CommonAppActivity.objects.filter(applicant=applicant).order_by('order'))
    ca_honors = list(CommonAppHonor.objects.filter(applicant=applicant).order_by('order'))
    ca_count = len(ca_activities)
    honor_count = len(ca_honors)

    # Personal essay (get or create)
    essay, _ = CommonAppEssay.objects.get_or_create(applicant=applicant)

    return render(request, 'colleges/applications_common.html', {
        'colleges': colleges,
        'ca_activities': ca_activities,
        'ca_honors': ca_honors,
        'ca_count': ca_count,
        'honor_count': honor_count,
        'essay': essay,
        'prompts': [(i + 1, p) for i, p in enumerate(COMMON_APP_PROMPTS)],
        'status_choices': CommonAppEssay.STATUS_CHOICES,
    })

