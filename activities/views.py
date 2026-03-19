from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import UCEntryForm, CommonAppActivityForm, CommonAppHonorForm, MITEntryForm
from .models import UCEntry, CommonAppActivity, CommonAppHonor, MITEntry
from core.models import CoreActivity, Applicant


def _get_cross_links(core_activity, exclude_model=None, exclude_pk=None):
    """Build cross-format links for an activity hub entry."""
    linked = []
    if not core_activity:
        return linked
    for uc in core_activity.uc_entries.all():
        if exclude_model == 'uc' and uc.pk == exclude_pk:
            continue
        linked.append(('UC', uc.name, reverse('activities:uc_edit', args=[uc.pk])))
    for ca in core_activity.common_app_activities.all():
        if exclude_model == 'ca' and ca.pk == exclude_pk:
            continue
        linked.append(('Common App', ca.organization or ca.position, reverse('activities:ca_edit', args=[ca.pk])))
    for h in core_activity.common_app_honors.all():
        if exclude_model == 'honor' and h.pk == exclude_pk:
            continue
        linked.append(('Honor', h.title, reverse('activities:honor_edit', args=[h.pk])))
    for m in core_activity.mit_entries.all():
        if exclude_model == 'mit' and m.pk == exclude_pk:
            continue
        linked.append(('MIT', m.org_name, reverse('activities:mit_edit', args=[m.pk])))
    return linked


def _prefetch_core_activities(applicant):
    qs = list(
        CoreActivity.objects.filter(applicant=applicant).order_by('order')
        .prefetch_related('uc_entries', 'common_app_activities', 'common_app_honors', 'mit_entries')
    )
    for a in qs:
        a.uc_entry = next(iter(a.uc_entries.all()), None)
        a.ca_entry = next(iter(a.common_app_activities.all()), None)
        a.honor_entry = next(iter(a.common_app_honors.all()), None)
        a.mit_entry = next(iter(a.mit_entries.all()), None)
    return qs


def activities_home(request):
    tab = request.GET.get('tab', 'centralized')
    if tab == 'honors':
        tab = 'common_app'
    applicant = Applicant.objects.get(pk=1)
    context = {
        'tab': tab,
        'core_activities': _prefetch_core_activities(applicant),
        'core_activity_count': CoreActivity.objects.filter(applicant=applicant).count(),
        'uc_entries': UCEntry.objects.filter(applicant=applicant).select_related('core_activity'),
        'uc_count': UCEntry.objects.filter(applicant=applicant).count(),
        'uc_category_choices': UCEntry.CATEGORY_CHOICES,
        'common_app_activities': CommonAppActivity.objects.filter(applicant=applicant).select_related('core_activity'),
        'ca_count': CommonAppActivity.objects.filter(applicant=applicant).count(),
        'ca_type_choices': CommonAppActivity.ACTIVITY_TYPE_CHOICES,
        'common_app_honors': CommonAppHonor.objects.filter(applicant=applicant).select_related('core_activity'),
        'honor_count': CommonAppHonor.objects.filter(applicant=applicant).count(),
        'mit_entries': MITEntry.objects.filter(applicant=applicant).select_related('core_activity'),
        'mit_count': MITEntry.objects.filter(applicant=applicant).count(),
        'mit_category_choices': MITEntry.CATEGORY_CHOICES,
        'mit_category_limits': MITEntry.CATEGORY_LIMITS,
    }
    if request.headers.get('HX-Request'):
        return render(request, 'activities/_tab_content.html', context)
    return render(request, 'activities/home.html', context)


# ── UC Entry CRUD ──

def uc_add(request):
    if request.method == 'POST':
        form = UCEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.order = UCEntry.objects.count()
            entry.save()
            return redirect('activities:home')
    else:
        form = UCEntryForm()
    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': 'Add UC Activity/Award',
        'back_url': 'activities:home', 'back_tab': 'uc',
        'char_fields': {'background': 250, 'description': 350},
    })


def uc_edit(request, pk):
    entry = get_object_or_404(UCEntry, pk=pk)
    if request.method == 'POST':
        form = UCEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('activities:home')
    else:
        form = UCEntryForm(instance=entry)

    linked = _get_cross_links(entry.core_activity, 'uc', entry.pk)

    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': f'Edit UC: {entry.name}',
        'back_url': 'activities:home', 'back_tab': 'uc',
        'entry': entry, 'linked': linked,
        'char_fields': {'background': 250, 'description': 350},
    })


def uc_cell(request, pk, field):
    entry = get_object_or_404(UCEntry, pk=pk)
    ctx = {'entry': entry, 'uc_category_choices': UCEntry.CATEGORY_CHOICES}
    if request.method == 'POST':
        if field in ('name', 'background', 'description', 'hours_per_week', 'weeks_per_year'):
            setattr(entry, field, request.POST.get('value', ''))
            entry.save()
        elif field == 'category':
            entry.category = request.POST.get('value', '')
            entry.save()
        elif field == 'grades':
            entry.grade_9 = 'grade_9' in request.POST
            entry.grade_10 = 'grade_10' in request.POST
            entry.grade_11 = 'grade_11' in request.POST
            entry.grade_12 = 'grade_12' in request.POST
            entry.save()
        return render(request, 'activities/_uc_row.html', ctx)
    return render(request, 'activities/_uc_row.html', {**ctx, 'editing': field})


@require_POST
def uc_delete(request, pk):
    get_object_or_404(UCEntry, pk=pk).delete()
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    return redirect('activities:home')


# ── Common App Activity CRUD ──

def ca_add(request):
    if request.method == 'POST':
        form = CommonAppActivityForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.order = CommonAppActivity.objects.count()
            entry.save()
            return redirect('/activities/?tab=common_app')
    else:
        form = CommonAppActivityForm()
    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': 'Add Common App Activity',
        'back_url': 'activities:home', 'back_tab': 'common_app',
        'char_fields': {'position': 50, 'organization': 100, 'description': 150},
    })


def ca_edit(request, pk):
    entry = get_object_or_404(CommonAppActivity, pk=pk)
    if request.method == 'POST':
        form = CommonAppActivityForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('/activities/?tab=common_app')
    else:
        form = CommonAppActivityForm(instance=entry)

    linked = _get_cross_links(entry.core_activity, 'ca', entry.pk)

    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': f'Edit: {entry.organization or entry.position}',
        'back_url': 'activities:home', 'back_tab': 'common_app',
        'entry': entry, 'linked': linked,
        'char_fields': {'position': 50, 'organization': 100, 'description': 150},
    })


def ca_cell(request, pk, field):
    activity = get_object_or_404(CommonAppActivity, pk=pk)
    ctx = {'activity': activity, 'ca_type_choices': CommonAppActivity.ACTIVITY_TYPE_CHOICES}
    if request.method == 'POST':
        if field in ('position', 'organization', 'description'):
            setattr(activity, field, request.POST.get('value', ''))
            activity.save()
        elif field == 'activity_type':
            activity.activity_type = request.POST.get('value', '')
            activity.save()
        elif field in ('hours_per_week', 'weeks_per_year'):
            val = request.POST.get('value', '').strip()
            setattr(activity, field, int(val) if val.isdigit() else None)
            activity.save()
        elif field == 'grades':
            activity.grade_9 = 'grade_9' in request.POST
            activity.grade_10 = 'grade_10' in request.POST
            activity.grade_11 = 'grade_11' in request.POST
            activity.grade_12 = 'grade_12' in request.POST
            activity.save()
        elif field == 'timing':
            activity.timing_school = 'timing_school' in request.POST
            activity.timing_breaks = 'timing_breaks' in request.POST
            activity.timing_all_year = 'timing_all_year' in request.POST
            activity.save()
        return render(request, 'activities/_ca_row.html', ctx)
    return render(request, 'activities/_ca_row.html', {**ctx, 'editing': field})


@require_POST
def ca_delete(request, pk):
    get_object_or_404(CommonAppActivity, pk=pk).delete()
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    return redirect('/activities/?tab=common_app')


# ── Common App Honor CRUD ──

def honor_add(request):
    if request.method == 'POST':
        form = CommonAppHonorForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.order = CommonAppHonor.objects.count()
            entry.save()
            return redirect('/activities/?tab=honors')
    else:
        form = CommonAppHonorForm()
    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': 'Add Common App Honor',
        'back_url': 'activities:home', 'back_tab': 'honors',
        'char_fields': {},
    })


def honor_edit(request, pk):
    entry = get_object_or_404(CommonAppHonor, pk=pk)
    if request.method == 'POST':
        form = CommonAppHonorForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('/activities/?tab=honors')
    else:
        form = CommonAppHonorForm(instance=entry)

    linked = _get_cross_links(entry.core_activity, 'honor', entry.pk)

    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': f'Edit Honor: {entry.title}',
        'back_url': 'activities:home', 'back_tab': 'honors',
        'entry': entry, 'linked': linked,
        'char_fields': {},
    })


def honor_cell(request, pk, field):
    honor = get_object_or_404(CommonAppHonor, pk=pk)
    ctx = {'honor': honor}
    if request.method == 'POST':
        if field == 'title':
            honor.title = request.POST.get('value', '')
            honor.save()
        elif field == 'grades':
            honor.grade_9 = 'grade_9' in request.POST
            honor.grade_10 = 'grade_10' in request.POST
            honor.grade_11 = 'grade_11' in request.POST
            honor.grade_12 = 'grade_12' in request.POST
            honor.save()
        elif field == 'levels':
            honor.level_school = 'level_school' in request.POST
            honor.level_state_regional = 'level_state_regional' in request.POST
            honor.level_national = 'level_national' in request.POST
            honor.level_international = 'level_international' in request.POST
            honor.save()
        return render(request, 'activities/_honor_row.html', ctx)
    return render(request, 'activities/_honor_row.html', {**ctx, 'editing': field})


@require_POST
def honor_delete(request, pk):
    get_object_or_404(CommonAppHonor, pk=pk).delete()
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    return redirect('/activities/?tab=honors')


# ── MIT Entry CRUD ──

def mit_add(request):
    if request.method == 'POST':
        form = MITEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.order = MITEntry.objects.filter(category=entry.category).count()
            entry.save()
            return redirect('/activities/?tab=mit')
    else:
        form = MITEntryForm()
    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': 'Add MIT Entry',
        'back_url': 'activities:home', 'back_tab': 'mit',
        'char_fields': {},
        'word_fields': {'description': 40},
    })


def mit_edit(request, pk):
    entry = get_object_or_404(MITEntry, pk=pk)
    if request.method == 'POST':
        form = MITEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('/activities/?tab=mit')
    else:
        form = MITEntryForm(instance=entry)

    linked = _get_cross_links(entry.core_activity, 'mit', entry.pk)

    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': f'Edit MIT: {entry.org_name}',
        'back_url': 'activities:home', 'back_tab': 'mit',
        'entry': entry, 'linked': linked,
        'char_fields': {},
        'word_fields': {'description': 40},
    })


def mit_cell(request, pk, field):
    entry = get_object_or_404(MITEntry, pk=pk)
    ctx = {'entry': entry, 'mit_category_choices': MITEntry.CATEGORY_CHOICES}
    if request.method == 'POST':
        if field in ('org_name', 'role_award', 'participation_period', 'description'):
            setattr(entry, field, request.POST.get('value', ''))
            entry.save()
        elif field == 'category':
            entry.category = request.POST.get('value', '')
            entry.save()
        elif field in ('hours_per_week', 'weeks_per_year'):
            val = request.POST.get('value', '').strip()
            setattr(entry, field, int(val) if val.isdigit() else None)
            entry.save()
        return render(request, 'activities/_mit_row.html', ctx)
    return render(request, 'activities/_mit_row.html', {**ctx, 'editing': field})


@require_POST
def mit_delete(request, pk):
    get_object_or_404(MITEntry, pk=pk).delete()
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    return redirect('/activities/?tab=mit')


# ── Exports ──

def _grades(obj):
    grades = []
    if obj.grade_9: grades.append('9th')
    if obj.grade_10: grades.append('10th')
    if obj.grade_11: grades.append('11th')
    if obj.grade_12: grades.append('12th')
    return ', '.join(grades) if grades else '—'


def export_uc(request):
    applicant = Applicant.objects.get(pk=1)
    entries = UCEntry.objects.filter(applicant=applicant)
    lines = ['UC ACTIVITIES & AWARDS EXPORT', '=' * 40, '']
    for i, e in enumerate(entries, 1):
        lines += [
            f'Entry {i} of {entries.count()}: {e.name}',
            f'Category: {e.get_category_display()}',
            f'Grades: {_grades(e)}',
            f'Hours/week: {e.hours_per_week or "—"}    Weeks/year: {e.weeks_per_year or "—"}',
            f'Background ({len(e.background)}/250 chars):',
            f'  {e.background or "(empty)"}',
            f'Description ({len(e.description)}/350 chars):',
            f'  {e.description or "(empty)"}',
            '',
            '-' * 40,
            '',
        ]
    content = '\n'.join(lines)
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="uc_activities.txt"'
    return response


def export_common_app(request):
    applicant = Applicant.objects.get(pk=1)
    activities = CommonAppActivity.objects.filter(applicant=applicant)
    honors = CommonAppHonor.objects.filter(applicant=applicant)
    lines = ['COMMON APP ACTIVITIES & HONORS EXPORT', '=' * 40, '']

    lines += [f'ACTIVITIES ({activities.count()}/10)', '']
    for i, a in enumerate(activities, 1):
        timing = []
        if a.timing_school: timing.append('During school year')
        if a.timing_breaks: timing.append('School breaks')
        if a.timing_all_year: timing.append('All year')
        lines += [
            f'Activity {i}: {a.organization or "(no org)"}',
            f'Type: {a.get_activity_type_display()}',
            f'Position/Leadership ({len(a.position)}/50 chars): {a.position or "—"}',
            f'Organization ({len(a.organization)}/100 chars): {a.organization or "—"}',
            f'Grades: {_grades(a)}',
            f'Timing: {", ".join(timing) or "—"}',
            f'Hours/week: {a.hours_per_week or "—"}    Weeks/year: {a.weeks_per_year or "—"}',
            f'Description ({len(a.description)}/150 chars):',
            f'  {a.description or "(empty)"}',
            '',
            '-' * 40,
            '',
        ]

    lines += [f'HONORS ({honors.count()}/5)', '']
    for i, h in enumerate(honors, 1):
        levels = []
        if h.level_school: levels.append('School')
        if h.level_state_regional: levels.append('State/Regional')
        if h.level_national: levels.append('National')
        if h.level_international: levels.append('International')
        lines += [
            f'Honor {i}: {h.title}',
            f'Grades: {_grades(h)}',
            f'Recognition Level: {", ".join(levels) or "—"}',
            '',
            '-' * 40,
            '',
        ]

    content = '\n'.join(lines)
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="common_app_activities.txt"'
    return response


def export_mit(request):
    applicant = Applicant.objects.get(pk=1)
    entries = MITEntry.objects.filter(applicant=applicant)
    lines = ['MIT ENTRIES EXPORT', '=' * 40, '']
    category_order = ['job', 'activity', 'summer', 'scholastic', 'non_scholastic']
    category_labels = dict(MITEntry.CATEGORY_CHOICES)
    category_limits = MITEntry.CATEGORY_LIMITS
    for cat in category_order:
        cat_entries = [e for e in entries if e.category == cat]
        label = category_labels.get(cat, cat).upper() + 'S'
        limit = category_limits.get(cat, '?')
        lines += [f'{label} ({len(cat_entries)}/{limit})', '']
        if cat_entries:
            for i, e in enumerate(cat_entries, 1):
                lines += [
                    f'  Entry {i}: {e.org_name or "(no org)"}',
                    f'  Role/Award: {e.role_award or "—"}',
                    f'  Period: {e.participation_period or "—"}',
                    f'  Hours/week: {e.hours_per_week or "—"}    Weeks/year: {e.weeks_per_year or "—"}',
                    f'  Description (40 word limit):',
                    f'    {e.description or "(empty)"}',
                    '',
                ]
        else:
            lines += ['  (none)', '']
        lines += ['-' * 40, '']

    content = '\n'.join(lines)
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="mit_entries.txt"'
    return response
