from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CollegeForm
from .models import College


# Fields shown in the main table (in display order)
TABLE_FIELDS = [
    ('name', 'College Name'),
    ('apply_status', 'Status'),
    ('tier', 'Tier'),
    ('acceptance_rate', 'Acc.'),
    ('location', 'Location'),
    ('app_platform', 'App'),
    ('terms', 'Terms'),
    ('ea_deadline', 'EA'),
    ('ed1_deadline', 'ED I'),
    ('rd_deadline', 'RD'),
    ('intended_major', 'Major'),
    ('applicant_notes', 'Notes'),
]

SORTABLE_FIELDS = {f[0] for f in TABLE_FIELDS}


def college_list(request):
    colleges = College.objects.all()

    # Sorting
    sort = request.GET.get('sort', '')
    sort_dir = request.GET.get('dir', 'asc')
    if sort in SORTABLE_FIELDS:
        order = sort if sort_dir == 'asc' else f'-{sort}'
        colleges = colleges.order_by(order)

    # Filtering
    status_filter = request.GET.get('status', '')
    if status_filter:
        colleges = colleges.filter(apply_status=status_filter)

    platform_filter = request.GET.get('platform', '')
    if platform_filter:
        colleges = colleges.filter(app_platform__icontains=platform_filter)

    search = request.GET.get('q', '')
    if search:
        colleges = colleges.filter(name__icontains=search)

    context = {
        'colleges': colleges,
        'table_fields': TABLE_FIELDS,
        'sort': sort,
        'sort_dir': sort_dir,
        'status_filter': status_filter,
        'platform_filter': platform_filter,
        'search': search,
        'status_choices': College.APPLY_STATUS_CHOICES,
    }

    # htmx partial: just return the table body
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
                    'college': college, 'table_fields': TABLE_FIELDS
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

    if field not in SORTABLE_FIELDS:
        return HttpResponse('Invalid field', status=400)

    if request.method == 'POST':
        value = request.POST.get('value', '')
        setattr(college, field, value)
        college.save()
        return render(request, 'colleges/_college_row.html', {
            'college': college, 'table_fields': TABLE_FIELDS
        })

    # GET: return the edit form for this cell
    current_value = getattr(college, field, '')
    field_label = dict(TABLE_FIELDS).get(field, field)

    # Use a select for apply_status, text input for everything else
    if field == 'apply_status':
        return render(request, 'colleges/_cell_edit_select.html', {
            'college': college, 'field': field, 'field_label': field_label,
            'current_value': current_value, 'choices': College.APPLY_STATUS_CHOICES,
            'table_fields': TABLE_FIELDS,
        })

    return render(request, 'colleges/_cell_edit.html', {
        'college': college, 'field': field, 'field_label': field_label,
        'current_value': current_value, 'table_fields': TABLE_FIELDS,
    })


def college_add(request):
    if request.method == 'POST':
        form = CollegeForm(request.POST)
        if form.is_valid():
            college = form.save(commit=False)
            college.order = College.objects.count()
            college.save()
            if request.headers.get('HX-Request'):
                colleges = College.objects.all()
                return render(request, 'colleges/_college_table.html', {
                    'colleges': colleges, 'table_fields': TABLE_FIELDS,
                    'status_choices': College.APPLY_STATUS_CHOICES,
                })
            return redirect('colleges:list')
    else:
        form = CollegeForm()

    return render(request, 'colleges/college_add.html', {'form': form})


@require_POST
def college_delete(request, pk):
    college = get_object_or_404(College, pk=pk)
    college.delete()
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    return redirect('colleges:list')
