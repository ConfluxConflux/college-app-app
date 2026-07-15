import json
from collections import defaultdict
from urllib.parse import urlparse

from django.core.paginator import Paginator

from django.db.models import (
    Case, When, Value, IntegerField, FloatField, F, OuterRef, Q, Subquery,
)
from django.db.models.functions import Cast, Coalesce, Lower, NullIf, Replace
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

from .models import (
    APPLICATION_ROUND_CHOICES,
    APPLY_STATUS_CHOICES,
    DIFFICULTY_CHOICES,
    College,
    UserCollege,
)
from activities.models import UCEntry, CommonAppActivity, CommonAppHonor, MITEntry
from core.models import Applicant
from supplements.models import (
    ESSAY_STATUS_CHOICES,
    SupplementEssay,
    UCPersonalInsightQuestion,
    CommonAppEssay,
    UC_PIQ_PROMPTS,
    COMMON_APP_PROMPTS,
)


# Always visible. Everything else is off until you ask for it — the blank
# slate is the point, and a wall of columns is what the competitors do.
DEFAULT_FIELDS = [
    ('name', 'College'),
    ('apply_status', 'Status'),
    ('applicant_notes', 'Notes'),
]

# Optional columns the user can toggle on
OPTIONAL_FIELDS = [
    ('application_round', 'Round'),
    ('deadline', 'Deadline'),
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

# Fields the UI edits through a <select>. The cell editor setattr()s whatever
# it is posted, so without this any string reaches the column — and a bogus
# application_round in particular would resolve the deadline to the RD date
# without being marked a fallback, i.e. quietly showing the wrong date.
CHOICE_FIELDS = {
    'apply_status': APPLY_STATUS_CHOICES,
    'difficulty': DIFFICULTY_CHOICES,
    'application_round': APPLICATION_ROUND_CHOICES,
}

# The two views and which statuses they show
VIEWS = {
    'applications': {
        'label': 'Your List',
        'statuses': ['applying', 'likely', 'considering', 'unlikely', 'applied', 'deferred', 'waitlisted', 'rejected', 'enrolled', 'withdrawn', 'accepted'],  # everything except not_applying
    },
    'all': {
        'label': 'All Colleges',
        'statuses': None,  # no filter
    },
}

# Sort order by relevance: Applying → Considering → Deferred → Waitlisted → Submitted → Accepted → Rejected
_RELEVANCE_ORDER = Case(
    When(apply_status='applying',    then=Value(1)),
    When(apply_status='likely',      then=Value(2)),
    When(apply_status='considering', then=Value(3)),
    When(apply_status='unlikely',    then=Value(4)),
    When(apply_status='deferred',    then=Value(5)),
    When(apply_status='waitlisted',  then=Value(6)),
    When(apply_status='applied',     then=Value(7)),
    When(apply_status='accepted',    then=Value(8)),
    When(apply_status='enrolled',    then=Value(9)),
    When(apply_status='rejected',    then=Value(10)),
    When(apply_status='withdrawn',   then=Value(11)),
    When(apply_status='not_applying',then=Value(12)),
    default=Value(13),
    output_field=IntegerField(),
)

APP_PROGRESS_STATUS_ORDER = _RELEVANCE_ORDER
STATUS_ORDER = _RELEVANCE_ORDER


# Solid dot colors per status for the map (the darker pill text colors).
STATUS_DOT_COLOR = {
    'considering': '#4a3a9c',
    'applying':    '#1a4a9c',
    'likely':      '#1a5a9c',
    'unlikely':    '#8c2020',
    'applied':     '#1e5c20',
    'accepted':    '#246024',
    'deferred':    '#7a6000',
    'waitlisted':  '#7a4a00',
    'rejected':    '#8c1a1a',
    'enrolled':    '#1a5c70',
    'withdrawn':   '#5a4038',
}


def college_map(request):
    """Map tab: plots the applicant's list colleges (those with coordinates),
    color-coded by application status."""
    applicant = request.user.applicant
    status_labels = dict(UserCollege.APPLY_STATUS_CHOICES)

    all_colleges = (UserCollege.objects
                    .filter(applicant=applicant)
                    .select_related('college'))

    points = []   # actively applying/considering/etc — colored by status
    other = []    # your not-applying colleges — gray, still openable in applications
    missing = []  # active but no coordinates (e.g. international)
    for uc in all_colleges:
        active = uc.apply_status not in ('', 'not_applying')
        if uc.latitude is None or uc.longitude is None:
            if active:
                missing.append(uc.name)
            continue
        if active:
            points.append({
                'pk': uc.pk,
                'name': uc.name,
                'city': uc.city,
                'state': uc.state,
                'status': status_labels.get(uc.apply_status, uc.apply_status),
                'color': STATUS_DOT_COLOR.get(uc.apply_status, '#666666'),
                'lat': uc.latitude,
                'lon': uc.longitude,
            })
        else:
            other.append({
                'pk': uc.pk,
                'name': uc.name,
                'city': uc.city,
                'state': uc.state,
                'lat': uc.latitude,
                'lon': uc.longitude,
            })

    # Legend: only statuses actually present, in relevance order.
    present = {p['status'] for p in points}
    legend = []
    for value, label in UserCollege.APPLY_STATUS_CHOICES:
        if label in present and value in STATUS_DOT_COLOR:
            legend.append({'label': label, 'color': STATUS_DOT_COLOR[value]})

    return render(request, 'colleges/college_map.html', {
        'current_view': 'map',
        'map_points': points,
        'other_points': other,
        'missing': missing,
        'legend': legend,
        'applications_url': reverse('applications:home'),
    })


def college_browse(request):
    """All Colleges: the same table as Your List, over every college.

    Your List is the schools you're working on. This is the database, so you
    can find one you hadn't thought of. It renders the identical row template —
    same Status dropdown, same Columns menu — because it is the same thing:
    most of these are simply Not Applying.

    Colleges you have no row for get a placeholder UserCollege that is never
    saved. Touching any cell creates it for real (see college_canonical_cell).
    Materialising 2,504 rows per user just to look at a list is the duplication
    the canonical/UserCollege split exists to avoid.

    Ordered by status first, in the same meaning-order Your List uses, so the
    colleges you're actually applying to stay on top. Everything you've never
    touched counts as Not Applying, and that block — nearly the whole table —
    is certified first, then the rest, both alphabetical.
    """
    applicant = request.user.applicant

    # The status is on UserCollege, but the rows are Colleges, so it has to be
    # pulled across. Never touched reads as Not Applying, which is true.
    # order_by('pk') because a college can have more than one UserCollege for
    # the same applicant (Jacob's list had Colorado State twice, under two
    # names). Without it the subquery and the row below pick different rows,
    # so the sort key and the name on screen disagree and the order looks
    # random.
    mine_qs = UserCollege.objects.filter(
        applicant=applicant, college=OuterRef('pk')
    ).order_by('pk')
    qs = College.objects.annotate(
        my_status=Subquery(mine_qs.values('apply_status')[:1]),
        my_display=Subquery(mine_qs.values('display_name')[:1]),
        certified=CERTIFIED_FIRST_CANONICAL,
        status_rank=STATUS_ORDER_CANONICAL,
    ).annotate(
        # Sort by the name actually on screen. The table shows display_name
        # when you have one ("Caltech"), so ordering by College.name sorts by
        # a string nobody can see and looks random.
        shown_name=Lower(Coalesce(NullIf('my_display', Value('')), 'name')),
    )

    search = request.GET.get('q', '').strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(city__icontains=search)
                       | Q(state__icontains=search))

    qs = qs.order_by('status_rank', 'certified', 'shown_name')

    # 2,504 rows is too many for one page, and nobody scrolls that far.
    paginator = Paginator(qs, 100)
    page = paginator.get_page(request.GET.get('page'))

    # One query for the user's colleges, matched in Python. A lookup per row
    # would be 100 extra queries a page.
    # Same order as the subquery above, and first-wins, so the row shown is the
    # row sorted on.
    mine = {}
    for uc in UserCollege.objects.filter(
        applicant=applicant, college__in=[c.pk for c in page.object_list]
    ).select_related('college').order_by('pk'):
        mine.setdefault(uc.college_id, uc)
    rows = []
    for c in page.object_list:
        uc = mine.get(c.pk)
        if uc is None:
            # Unsaved: a college you've never touched isn't a row you own.
            uc = UserCollege(applicant=applicant, college=c, apply_status='not_applying')
        rows.append(uc)

    querystring = request.GET.copy()
    querystring.pop('page', None)

    return render(request, 'colleges/college_list.html', {
        'colleges': rows,
        'page': page,
        'is_browse': True,
        # Every row here has a canonical college, so cells address it by
        # College pk and the UserCollege is created on first edit.
        'use_canonical_urls': True,
        'reorderable': False,
        'table_fields': ALL_TABLE_FIELDS,
        'optional_fields': OPTIONAL_FIELDS,
        'optional_field_names': {f[0] for f in OPTIONAL_FIELDS},
        'sort': '',
        'sort_dir': 'asc',
        'status_filter': '',
        'search': search,
        'status_choices': [
            (v, l) for v, l in UserCollege.APPLY_STATUS_CHOICES
            if v not in {'likely', 'unlikely', 'enrolled', 'withdrawn'}
        ],
        'current_view': 'all',
        'views': VIEWS,
        'platform_tracker': _build_platform_tracker(applicant),
        'tab_url': reverse('colleges:list_all'),
        'total': paginator.count,
        'querystring': querystring.urlencode(),
    })


@require_http_methods(['GET', 'POST'])
def college_canonical_cell(request, college_pk, field):
    """Edit a cell on All Colleges, addressing the college by its canonical pk.

    Creates the UserCollege on first touch. Browsing 2,504 colleges shouldn't
    write 2,504 rows; deciding something about one should write exactly one.
    """
    applicant = request.user.applicant
    canonical = get_object_or_404(College, pk=college_pk)
    uc, _created = UserCollege.objects.get_or_create(
        applicant=applicant, college=canonical,
        defaults={
            'apply_status': 'not_applying',
            'order': UserCollege.objects.filter(applicant=applicant).count(),
        },
    )
    return college_edit_cell(request, uc.pk, field)


def college_list(request, tab='applications'):
    current_view = tab if tab in VIEWS else 'applications'
    if current_view == 'all':
        return college_browse(request)

    applicant = request.user.applicant
    view_config = VIEWS[current_view]
    colleges = UserCollege.objects.filter(applicant=applicant)

    # Apply view filter
    if view_config['statuses']:
        colleges = colleges.filter(apply_status__in=view_config['statuses'])

    sort = request.GET.get('sort', '')
    sort_dir = request.GET.get('dir', 'asc')
    if sort in EDITABLE_FIELDS:
        if sort in SORT_ANNOTATIONS:
            colleges = colleges.annotate(_sortkey=SORT_ANNOTATIONS[sort]())
            db_field = '_sortkey'
        else:
            db_field = sort
        # nulls_last so blanks sink instead of leading the list — and so SQLite
        # (nulls first) and Postgres (nulls last) agree.
        key = F(db_field)
        colleges = colleges.order_by(
            key.asc(nulls_last=True) if sort_dir == 'asc' else key.desc(nulls_last=True)
        )
    elif current_view == 'all':
        # Jacob-certified alphabetically, then everything else alphabetically.
        colleges = colleges.annotate(certified=CERTIFIED_FIRST, eff_name=effective_name()) \
                           .order_by('certified', 'eff_name')
    elif current_view == 'applications':
        # Your arrangement is the home state; sorting is a lens over it.
        colleges = colleges.order_by('order')

    # Search (display_name if set, else canonical name)
    search = request.GET.get('q', '')
    if search:
        colleges = colleges.filter(
            Q(display_name__icontains=search) | Q(college__name__icontains=search)
        )

    # Status sub-filter (within the current view's statuses)
    status_filter = request.GET.get('status', '')
    if status_filter:
        colleges = colleges.filter(apply_status=status_filter)

    platform_tracker = _build_platform_tracker(applicant)

    # Status choices for the filter dropdown — limit to current view's statuses, exclude hidden statuses
    HIDDEN_STATUSES = {'likely', 'unlikely', 'enrolled', 'withdrawn'}
    all_choices = dict(UserCollege.APPLY_STATUS_CHOICES)
    if view_config['statuses']:
        view_status_choices = [(v, all_choices[v]) for v in view_config['statuses'] if v in all_choices and v not in HIDDEN_STATUSES]
    else:
        view_status_choices = [(v, l) for v, l in UserCollege.APPLY_STATUS_CHOICES if v not in HIDDEN_STATUSES]

    tab_url_map = {'applications': 'colleges:list', 'all': 'colleges:list_all'}
    from django.urls import reverse
    tab_url = reverse(tab_url_map.get(current_view, 'colleges:list'))

    # Rows can only be hand-placed when nothing else is deciding the order.
    reorderable = current_view == 'applications' and not sort and not search and not status_filter

    context = {
        'colleges': colleges,
        'reorderable': reorderable,
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
        'tab_url': tab_url,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'colleges/_college_table.html', context)

    return render(request, 'colleges/college_list.html', context)


def effective(field, canonical=None):
    """Annotation for a text override falling back to its canonical College value.

    Mirrors the property fallback in the model, but in SQL, so it can be
    filtered and sorted on. An override of '' means "unset", not "empty".
    """
    canonical = canonical or field
    return Coalesce(
        NullIf(field + '_override', Value('')),
        NullIf('college__' + canonical, Value('')),
        Value(''),
    )


def effective_num(field, canonical=None):
    """Same as effective(), for numeric fields where NULL already means unset."""
    canonical = canonical or field
    return Coalesce(field + '_override', 'college__' + canonical)


def effective_pct(field):
    """A percentage stored as text ('8.7%'), as a number, for sorting.

    Sorting these as strings puts 3.5% after 27.8%. Every stored value matches
    NN.N% or is empty; NullIf keeps the empty ones from blowing up the cast on
    Postgres, where CAST('' AS float) is an error rather than 0.
    """
    return Cast(
        NullIf(Replace(effective(field), Value('%'), Value('')), Value('')),
        FloatField(),
    )


def effective_name():
    """What uc.name resolves to: display_name if set, else the canonical name.

    Lowercased so "alphabetical" means the same thing on SQLite (BINARY
    collation, uppercase first: 'MIT' < 'McGill') as on Postgres in prod.
    """
    return Lower(Coalesce(NullIf('display_name', Value('')), 'college__name', Value('')))


# Sorting on a *_override column alone ignores canonical data entirely, which
# is every college now that IPEDS is imported and redundant overrides pruned.
SORT_ANNOTATIONS = {
    'name': effective_name,
    # Status has a meaning-order, not an alphabet-order: Applying comes before
    # Considering because that is how much it matters, not because A < C.
    # Without this the header sorted the raw values as strings.
    'apply_status': lambda: _RELEVANCE_ORDER,
    'acceptance_rate': lambda: effective_pct('acceptance_rate'),
    'app_platform': lambda: effective('app_platform'),
    'terms': lambda: effective('academic_calendar', 'academic_calendar'),
    'ea_deadline': lambda: effective('ea_deadline'),
    'ed1_deadline': lambda: effective('ed1_deadline'),
    'ed2_deadline': lambda: effective('ed2_deadline'),
    'rd_deadline': lambda: effective('rd_deadline'),
    'sat_avg': lambda: effective_num('sat_avg'),
    'undergrad_enrollment': lambda: effective_num('undergrad_enrollment'),
    # The cached cycle ordinal, so "sort by deadline" puts Nov 30 before Jan 1
    # instead of sorting '11/30' and '1/1' as strings.
    'deadline': lambda: F('deadline_ordinal'),
}

# Jacob-certified first (someone he knows got in), then the IPEDS bulk.
CERTIFIED_FIRST = Case(
    When(college__proof_acceptances__gt=0, then=Value(0)),
    default=Value(1),
    output_field=IntegerField(),
)
# Same, from College itself rather than through UserCollege.
CERTIFIED_FIRST_CANONICAL = Case(
    When(proof_acceptances__gt=0, then=Value(0)),
    default=Value(1),
    output_field=IntegerField(),
)

# _RELEVANCE_ORDER over an annotated my_status, for All Colleges. A college
# you've never touched has no row at all, so NULL falls to the default and
# reads as Not Applying — which is what it is.
STATUS_ORDER_CANONICAL = Case(
    When(my_status='applying',    then=Value(1)),
    When(my_status='likely',      then=Value(2)),
    When(my_status='considering', then=Value(3)),
    When(my_status='unlikely',    then=Value(4)),
    When(my_status='deferred',    then=Value(5)),
    When(my_status='waitlisted',  then=Value(6)),
    When(my_status='applied',     then=Value(7)),
    When(my_status='accepted',    then=Value(8)),
    When(my_status='enrolled',    then=Value(9)),
    When(my_status='rejected',    then=Value(10)),
    When(my_status='withdrawn',   then=Value(11)),
    default=Value(12),
    output_field=IntegerField(),
)


def _build_platform_tracker(applicant):
    APPLYING_STATUSES = {'applying', 'applied', 'deferred', 'waitlisted', 'accepted', 'enrolled'}
    CONSIDERING_STATUSES = {'considering'}
    qs = UserCollege.objects.filter(applicant=applicant).annotate(eff_platform=effective('app_platform'))
    applying_platforms = set(
        qs.filter(apply_status__in=APPLYING_STATUSES).values_list('eff_platform', flat=True)
    )
    considering_platforms = set(
        qs.filter(apply_status__in=CONSIDERING_STATUSES).values_list('eff_platform', flat=True)
    )
    def _state(key):
        # Exact match: substring matching made 'uc' match 'ucas', lighting up
        # the UC tracker for UK schools.
        if key in applying_platforms:
            return 'applying'
        if key in considering_platforms:
            return 'considering'
        return 'none'
    mit = qs.filter(eff_platform='mit').first()
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


def college_edit_cell(request, pk, field):
    """Inline cell editing via htmx."""
    college = get_object_or_404(UserCollege, pk=pk, applicant=request.user.applicant)

    if field not in EDITABLE_FIELDS:
        return HttpResponse('Invalid field', status=400)

    if request.method == 'POST':
        value = request.POST.get('value', '')
        if field in CHOICE_FIELDS and value:
            if value not in {v for v, _ in CHOICE_FIELDS[field]}:
                return HttpResponse(f'Invalid {field}', status=400)
        setattr(college, field, value)
        college.save()
        ctx = {'college': college, 'table_fields': ALL_TABLE_FIELDS, 'optional_field_names': {f[0] for f in OPTIONAL_FIELDS}}
        if field == 'apply_status':
            applicant = request.user.applicant
            ctx['platform_tracker'] = _build_platform_tracker(applicant)
            return render(request, 'colleges/_college_row_with_tracker.html', ctx)
        return render(request, 'colleges/_college_row.html', ctx)

    current_value = getattr(college, field, '')
    field_label = ALL_TABLE_FIELDS_DICT.get(field, field)

    if field == 'apply_status':
        hidden = {'likely', 'unlikely', 'enrolled', 'withdrawn'}
        choices = [(v, l) for v, l in UserCollege.APPLY_STATUS_CHOICES if v not in hidden]
        return render(request, 'colleges/_cell_edit_select.html', {
            'college': college, 'field': field, 'field_label': field_label,
            'current_value': current_value, 'choices': choices,
            'table_fields': ALL_TABLE_FIELDS,
        })

    if field == 'difficulty':
        return render(request, 'colleges/_cell_edit_select.html', {
            'college': college, 'field': field, 'field_label': field_label,
            'current_value': current_value, 'choices': UserCollege.DIFFICULTY_CHOICES,
            'table_fields': ALL_TABLE_FIELDS,
        })

    return render(request, 'colleges/_cell_edit.html', {
        'college': college, 'field': field, 'field_label': field_label,
        'current_value': current_value, 'table_fields': ALL_TABLE_FIELDS,
    })


@require_POST
def college_add_row(request):
    """Add a college the canonical database doesn't have.

    Reached from the add-college modal when a search returns nothing. The row
    has no College FK, so every field is the user's own — that is what a custom
    college is.
    """
    applicant = request.user.applicant
    name = request.POST.get('name', '').strip()
    if not name:
        return HttpResponse('A name is required', status=400)

    college = UserCollege.objects.create(
        applicant=applicant,
        display_name=name,
        apply_status='applying',
        order=UserCollege.objects.filter(applicant=applicant).count(),
    )
    ctx = {
        'college': college,
        'table_fields': ALL_TABLE_FIELDS,
        'optional_field_names': {f[0] for f in OPTIONAL_FIELDS},
        'platform_tracker': _build_platform_tracker(applicant),
    }
    response = render(request, 'colleges/_college_row_with_tracker.html', ctx)
    response['HX-Trigger'] = 'college-added'
    return response


def college_json(request):
    """JSON endpoint for Tabulator data loading."""
    current_view = request.GET.get('view', 'applications')
    if current_view not in VIEWS:
        current_view = 'applications'

    applicant = request.user.applicant
    view_config = VIEWS[current_view]
    colleges = UserCollege.objects.filter(applicant=applicant)

    if view_config['statuses']:
        colleges = colleges.filter(apply_status__in=view_config['statuses'])

    search = request.GET.get('q', '')
    if search:
        colleges = colleges.filter(
            Q(display_name__icontains=search) | Q(college__name__icontains=search)
        )

    if current_view == 'all':
        colleges = colleges.annotate(status_order=STATUS_ORDER).order_by('status_order', 'college__name')

    status_display = dict(UserCollege.APPLY_STATUS_CHOICES)
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
    college = get_object_or_404(UserCollege, pk=pk, applicant=request.user.applicant)
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


def college_search_suggestions(request):
    """Search canonical College objects for the add-college modal."""
    from .models import College as CanonicalCollege
    q = request.GET.get('q', '').strip()
    applicant = request.user.applicant

    if len(q) < 2:
        return render(request, 'colleges/_search_suggestions.html', {'suggestions': [], 'q': q})

    # "On your list" means any status except not_applying
    on_list = set(
        UserCollege.objects.filter(applicant=applicant)
        .exclude(college__isnull=True)
        .exclude(apply_status='not_applying')
        .values_list('college_id', flat=True)
    )

    suggestions = list(
        CanonicalCollege.objects.filter(name__icontains=q)
        .order_by('name')[:10]
    )

    return render(request, 'colleges/_search_suggestions.html', {
        'suggestions': suggestions,
        'on_list': on_list,
        'q': q,
    })


@require_POST
def college_quick_add(request):
    """Add a canonical college to the user's list from the search modal."""
    from .models import College as CanonicalCollege
    applicant = request.user.applicant
    college_pk = request.POST.get('college_pk')

    try:
        canonical = CanonicalCollege.objects.get(pk=college_pk)
    except (CanonicalCollege.DoesNotExist, ValueError, TypeError):
        return HttpResponse('College not found', status=404)

    try:
        uc = UserCollege.objects.get(applicant=applicant, college=canonical)
        if uc.apply_status == 'not_applying':
            # Re-add: promote from "not applying" to "applying"
            uc.apply_status = 'applying'
            uc.save()
        else:
            # Already actively on list — just close the modal
            response = HttpResponse('')
            response['HX-Trigger'] = 'college-added'
            return response
    except UserCollege.DoesNotExist:
        uc = UserCollege.objects.create(
            applicant=applicant,
            college=canonical,
            apply_status='applying',
            order=UserCollege.objects.filter(applicant=applicant).count(),
        )

    ctx = {
        'college': uc,
        'table_fields': ALL_TABLE_FIELDS,
        'optional_field_names': {f[0] for f in OPTIONAL_FIELDS},
        'platform_tracker': _build_platform_tracker(applicant),
    }
    response = render(request, 'colleges/_college_row_with_tracker.html', ctx)
    response['HX-Trigger'] = 'college-added'
    return response


@require_POST
def college_reorder(request):
    """Persist a drag-reorder of the college list.

    Takes the visible rows' pks in their new order. Your List hides
    not_applying colleges, so rather than renumbering 0..n-1 — which would
    drag hidden rows to the front — the visible rows are redistributed across
    the order slots they already occupy. Hidden rows keep their positions.
    """
    applicant = request.user.applicant
    try:
        pks = [int(p) for p in request.POST.getlist('pk')]
    except (TypeError, ValueError):
        return HttpResponse('Bad pk list', status=400)

    rows = {r.pk: r for r in UserCollege.objects.filter(applicant=applicant, pk__in=pks)}
    ordered = [rows[p] for p in pks if p in rows]
    if not ordered:
        return HttpResponse(status=204)

    slots = sorted(r.order for r in ordered)
    for slot, row in zip(slots, ordered):
        if row.order != slot:
            row.order = slot
            row.save(update_fields=['order'])
    return HttpResponse(status=204)


@require_POST
def college_remove(request, pk):
    """Take a college off Your List by marking it Not Applying.

    Deliberately not a delete. The college stays in All Colleges with its
    notes, essays and deadlines intact, so changing your mind costs nothing —
    searching for it again in the add modal promotes it back to Applying.

    On Your List the row is filtered out, so returning an empty body makes it
    disappear. On All Colleges the college still belongs there, so the row is
    re-rendered with its new status instead.
    """
    college = get_object_or_404(UserCollege, pk=pk, applicant=request.user.applicant)
    college.apply_status = 'not_applying'
    college.save()

    if not request.headers.get('HX-Request'):
        return redirect('colleges:list')

    current_url = request.headers.get('HX-Current-URL', '')
    on_all_colleges = urlparse(current_url).path.rstrip('/').endswith('/colleges/all')
    if on_all_colleges:
        return render(request, 'colleges/_college_row_with_tracker.html', {
            'college': college,
            'table_fields': ALL_TABLE_FIELDS,
            'optional_field_names': {f[0] for f in OPTIONAL_FIELDS},
            'platform_tracker': _build_platform_tracker(request.user.applicant),
        })
    return HttpResponse('')


APP_STATUS_ORDER_MAP = {
    'applying': 1, 'likely': 2, 'considering': 3, 'unlikely': 4,
    'deferred': 5, 'waitlisted': 6, 'applied': 7, 'accepted': 8,
    'enrolled': 9, 'rejected': 10, 'withdrawn': 11, 'not_applying': 12,
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
        UserCollege.objects.filter(applicant=applicant)
        .annotate(status_order=APP_PROGRESS_STATUS_ORDER, eff_name=effective_name())
        .order_by('status_order', 'eff_name')
    )

    APPLYING_STATUSES = {'applying', 'applied', 'deferred', 'waitlisted', 'accepted', 'enrolled'}
    CONSIDERING_STATUSES = {'considering'}
    applying_platforms = set(
        UserCollege.objects.filter(applicant=applicant, apply_status__in=APPLYING_STATUSES)
        .values_list('app_platform_override', flat=True)
    )
    considering_platforms = set(
        UserCollege.objects.filter(applicant=applicant, apply_status__in=CONSIDERING_STATUSES)
        .values_list('app_platform_override', flat=True)
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
    applicant = request.user.applicant
    colleges = _build_dropdown_colleges(applicant)

    selected = None
    selected_pk = request.GET.get('college')
    if selected_pk:
        try:
            pk_int = int(selected_pk)
            selected = UserCollege.objects.select_related('college').filter(applicant=applicant, pk=pk_int).first()
        except (ValueError, TypeError):
            pass

    # Status choices for the status badge dropdown
    status_choices = [
        ('not_applying', 'Not Applying'),
        ('considering', 'Considering'),
        ('applying', 'Applying'),
        ('applied', 'Submitted'),
        ('deferred', 'Deferred'),
        ('waitlisted', 'Waitlisted'),
        ('rejected', 'Rejected'),
        ('accepted', 'Accepted'),
    ]

    # Per-college dashboard data (only computed when a college is selected)
    essays = []
    essay_status_counts = []
    essay_done = essay_wip = essay_total = 0
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
        # Count each real status rather than deriving "not started" by
        # subtraction, which quietly lumped To Do, Idea Stage and Drafted
        # together the moment the status set grew.
        essay_status_counts = [
            {'key': key, 'label': label, 'count': sum(1 for e in essays if e.status == key)}
            for key, label in ESSAY_STATUS_CHOICES
        ]
        essay_done = sum(1 for e in essays if e.status == 'done')
        essay_wip = sum(1 for e in essays if e.status in ('wip', 'drafted'))

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
        platform_display = dict(UserCollege.APP_PLATFORM_CHOICES).get(platform, '') if platform else ''

        try:
            applicant = request.user.applicant
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
        'essay_status_counts': essay_status_counts,
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
    applicant = request.user.applicant
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
    applicant = request.user.applicant
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

