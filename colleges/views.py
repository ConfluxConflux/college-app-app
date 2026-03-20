import json

from django.db.models import Case, When, Value, IntegerField
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods

from .forms import CollegeForm
from .models import College


# Always-visible columns
DEFAULT_FIELDS = [
    ('name', 'College'),
    ('apply_status', 'Status'),
    ('applicant_notes', 'Notes'),
]

# Optional columns the user can toggle on
OPTIONAL_FIELDS = [
    ('tier', 'Tier'),
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
        'statuses': ['applied', 'deferred', 'waitlisted', 'rejected', 'enrolled'],
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
    default=Value(12),
    output_field=IntegerField(),
)

# Sort order for "All Colleges" view — most likely to apply first
STATUS_ORDER = Case(
    When(apply_status='applying', then=Value(1)),
    When(apply_status='likely', then=Value(2)),
    When(apply_status='considering', then=Value(3)),
    When(apply_status='unlikely', then=Value(4)),
    When(apply_status='not_applying', then=Value(5)),
    When(apply_status='applied', then=Value(6)),
    When(apply_status='deferred', then=Value(7)),
    When(apply_status='waitlisted', then=Value(8)),
    When(apply_status='rejected', then=Value(9)),
    When(apply_status='enrolled', then=Value(10)),
    default=Value(11),
    output_field=IntegerField(),
)


def college_list(request):
    current_view = request.GET.get('view', 'applications')
    if current_view not in VIEWS:
        current_view = 'applications'

    view_config = VIEWS[current_view]
    colleges = College.objects.all()

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
        'sort': sort,
        'sort_dir': sort_dir,
        'status_filter': status_filter,
        'search': search,
        'status_choices': view_status_choices,
        'current_view': current_view,
        'views': VIEWS,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'colleges/_college_table.html', context)

    return render(request, 'colleges/college_list.html', context)


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
        return render(request, 'colleges/_college_row.html', {
            'college': college, 'table_fields': ALL_TABLE_FIELDS
        })

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

    return render(request, 'colleges/_cell_edit.html', {
        'college': college, 'field': field, 'field_label': field_label,
        'current_value': current_value, 'table_fields': ALL_TABLE_FIELDS,
    })


def college_add(request):
    if request.method == 'POST':
        form = CollegeForm(request.POST)
        if form.is_valid():
            college = form.save(commit=False)
            college.order = College.objects.count()
            college.save()
            return redirect('colleges:list')
    else:
        form = CollegeForm()

    return render(request, 'colleges/college_add.html', {'form': form})


def college_json(request):
    """JSON endpoint for Tabulator data loading."""
    current_view = request.GET.get('view', 'applications')
    if current_view not in VIEWS:
        current_view = 'applications'

    view_config = VIEWS[current_view]
    colleges = College.objects.all()

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


def applications(request):
    colleges = College.objects.all().annotate(
        status_order=APP_PROGRESS_STATUS_ORDER
    ).order_by('status_order', 'name')

    selected = None
    selected_pk = request.GET.get('college')
    if selected_pk:
        try:
            selected = colleges.get(pk=int(selected_pk))
        except (College.DoesNotExist, ValueError):
            pass

    # Status choices in College List sort order (likely/unlikely hidden from users)
    status_choices = [
        ('applying', 'Applying'),
        ('considering', 'Considering'),
        ('not_applying', 'Not Applying'),
        ('applied', 'Submitted'),
        ('deferred', 'Deferred'),
        ('waitlisted', 'Waitlisted'),
        ('rejected', 'Rejected'),
        ('enrolled', 'Enrolled'),
        ('accepted', 'Accepted'),
    ]

    return render(request, 'colleges/applications.html', {
        'colleges': colleges,
        'selected': selected,
        'status_choices': status_choices,
    })

