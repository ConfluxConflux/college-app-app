import csv
import io
import json

from django.http import HttpResponse, JsonResponse
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


def redirect_to_uc(request):
    return redirect('activities:home_uc')


def activities_home(request, tab='uc'):
    applicant = Applicant.objects.get(pk=1)
    uc_entries_list = list(UCEntry.objects.filter(applicant=applicant).order_by('order').select_related('core_activity'))
    uc_slots = uc_entries_list[:20]
    while len(uc_slots) < 20:
        uc_slots.append(None)
    uc_overflow = uc_entries_list[20:]
    ca_entries_list = list(CommonAppActivity.objects.filter(applicant=applicant).order_by('order').select_related('core_activity'))
    ca_slots = ca_entries_list[:10]
    while len(ca_slots) < 10:
        ca_slots.append(None)
    ca_overflow = ca_entries_list[10:]

    honors_list = list(CommonAppHonor.objects.filter(applicant=applicant).order_by('order').select_related('core_activity'))
    honor_slots = honors_list[:5]
    while len(honor_slots) < 5:
        honor_slots.append(None)

    core_activities_list = _prefetch_core_activities(applicant)
    linked_uc_pks = {c.uc_entry.pk for c in core_activities_list if c.uc_entry}
    linked_ca_pks = {c.ca_entry.pk for c in core_activities_list if c.ca_entry}
    mit_entries_list = list(MITEntry.objects.filter(applicant=applicant).select_related('core_activity').order_by('category', 'order'))
    linked_mit_pks = {c.mit_entry.pk for c in core_activities_list if c.mit_entry}

    context = {
        'tab': tab,
        'core_activities': core_activities_list,
        'core_activity_count': CoreActivity.objects.filter(applicant=applicant).count(),
        'uc_slots': uc_slots,
        'uc_overflow': uc_overflow,
        'uc_count': len(uc_entries_list),
        'uc_category_choices': UCEntry.CATEGORY_CHOICES,
        'ca_slots': ca_slots,
        'ca_overflow': ca_overflow,
        'ca_count': len(ca_entries_list),
        'ca_type_choices': CommonAppActivity.ACTIVITY_TYPE_CHOICES,
        'honor_slots': honor_slots,
        'honor_count': len(honors_list),
        'mit_entries': mit_entries_list,
        'mit_count': MITEntry.objects.filter(applicant=applicant).count(),
        'mit_category_choices': MITEntry.CATEGORY_CHOICES,
        'mit_category_limits': MITEntry.CATEGORY_LIMITS,
        'orphaned_uc': [e for e in uc_entries_list if e.pk not in linked_uc_pks],
        'orphaned_ca': [e for e in ca_entries_list if e.pk not in linked_ca_pks],
        'orphaned_mit': [e for e in mit_entries_list if e.pk not in linked_mit_pks],
    }
    if request.headers.get('HX-Request'):
        return render(request, 'activities/_tab_content.html', context)
    return render(request, 'activities/home.html', context)


# ── UC Entry CRUD ──

def uc_add(request):
    if request.method == 'POST' and request.headers.get('HX-Request'):
        applicant = Applicant.objects.get(pk=1)
        entry = UCEntry.objects.create(
            applicant=applicant,
            category='extracurricular',
            name='',
            order=UCEntry.objects.filter(applicant=applicant).count(),
        )
        return render(request, 'activities/_uc_row.html', {
            'entry': entry,
            'uc_category_choices': UCEntry.CATEGORY_CHOICES,
        })
    if request.method == 'POST':
        form = UCEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.order = UCEntry.objects.count()
            entry.save()
            return redirect('activities:home_uc')
    else:
        form = UCEntryForm()
    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': 'Add UC Activity/Award',
        'back_href': reverse('activities:home_uc'), 'back_tab': 'uc',
        'char_fields': {'background': 250, 'description': 350},
    })


def uc_edit(request, pk):
    entry = get_object_or_404(UCEntry, pk=pk)
    if request.method == 'POST':
        form = UCEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('activities:home_uc')
    else:
        form = UCEntryForm(instance=entry)

    linked = _get_cross_links(entry.core_activity, 'uc', entry.pk)

    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': f'Edit UC: {entry.name}',
        'back_href': reverse('activities:home_uc'), 'back_tab': 'uc',
        'entry': entry, 'linked': linked,
        'char_fields': {'background': 250, 'description': 350},
    })


def uc_cell(request, pk, field):
    entry = get_object_or_404(UCEntry, pk=pk)
    ctx = {'entry': entry, 'uc_category_choices': UCEntry.CATEGORY_CHOICES}
    if request.method == 'POST':
        if field in ('name', 'background', 'description', 'hours_per_week', 'weeks_per_year', 'personal_notes'):
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
        elif field == 'recognition_levels':
            entry.level_school = 'level_school' in request.POST
            entry.level_city = 'level_city' in request.POST
            entry.level_state = 'level_state' in request.POST
            entry.level_regional = 'level_regional' in request.POST
            entry.level_national = 'level_national' in request.POST
            entry.level_international = 'level_international' in request.POST
            entry.save()
        elif field == 'is_academic':
            entry.is_academic = not entry.is_academic if entry.is_academic is not None else True
            entry.save()
        elif field == 'still_working':
            entry.still_working = not entry.still_working if entry.still_working is not None else True
            entry.save()
        return render(request, 'activities/_uc_row.html', ctx)
    return render(request, 'activities/_uc_row.html', {**ctx, 'editing': field})


@require_POST
def uc_delete(request, pk):
    get_object_or_404(UCEntry, pk=pk).delete()
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    return redirect('activities:home_uc')


@require_POST
def uc_slot_add(request, slot):
    """Create a new UCEntry for an empty slot, returned in edit mode."""
    field = request.POST.get('field', 'name')
    applicant = Applicant.objects.get(pk=1)
    entry = UCEntry.objects.create(
        applicant=applicant,
        order=slot,
        category='extracurricular',
    )
    ctx = {
        'entry': entry,
        'uc_category_choices': UCEntry.CATEGORY_CHOICES,
        'editing': field,
        'slot_num': slot,
    }
    return render(request, 'activities/_uc_row.html', ctx)


@require_POST
def uc_set_time(request, pk):
    """Set hours_per_week and weeks_per_year together (from estimator modal)."""
    entry = get_object_or_404(UCEntry, pk=pk)
    entry.hours_per_week = request.POST.get('hours_per_week', '').strip()
    entry.weeks_per_year = request.POST.get('weeks_per_year', '').strip()
    entry.save()
    return render(request, 'activities/_uc_row.html', {
        'entry': entry,
        'uc_category_choices': UCEntry.CATEGORY_CHOICES,
    })


@require_POST
def uc_reorder(request):
    applicant = Applicant.objects.get(pk=1)
    data = json.loads(request.body)
    for i, pk in enumerate(data.get('order', []), start=1):
        UCEntry.objects.filter(pk=pk, applicant=applicant).update(order=i)
    return HttpResponse(status=204)


# ── Common App Activity CRUD ──

def ca_add(request):
    if request.method == 'POST':
        form = CommonAppActivityForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.order = CommonAppActivity.objects.count()
            entry.save()
            return redirect('activities:home_common')
    else:
        form = CommonAppActivityForm()
    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': 'Add Common App Activity',
        'back_href': reverse('activities:home_common'), 'back_tab': 'common_app',
        'char_fields': {'position': 50, 'organization': 100, 'description': 150},
    })


def ca_edit(request, pk):
    entry = get_object_or_404(CommonAppActivity, pk=pk)
    if request.method == 'POST':
        form = CommonAppActivityForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('activities:home_common')
    else:
        form = CommonAppActivityForm(instance=entry)

    linked = _get_cross_links(entry.core_activity, 'ca', entry.pk)

    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': f'Edit: {entry.organization or entry.position}',
        'back_href': reverse('activities:home_common'), 'back_tab': 'common_app',
        'entry': entry, 'linked': linked,
        'char_fields': {'position': 50, 'organization': 100, 'description': 150},
    })


def ca_cell(request, pk, field):
    activity = get_object_or_404(CommonAppActivity, pk=pk)
    ctx = {'activity': activity, 'ca_type_choices': CommonAppActivity.ACTIVITY_TYPE_CHOICES}
    if request.method == 'POST':
        if field in ('position', 'organization', 'description', 'personal_notes'):
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
        elif field == 'similar_in_college':
            activity.similar_in_college = (
                not activity.similar_in_college
                if activity.similar_in_college is not None
                else True
            )
            activity.save()
        return render(request, 'activities/_ca_row.html', ctx)
    return render(request, 'activities/_ca_row.html', {**ctx, 'editing': field})


@require_POST
def ca_slot_add(request, slot):
    field = request.POST.get('field', 'organization')
    applicant = Applicant.objects.get(pk=1)
    activity = CommonAppActivity.objects.create(
        applicant=applicant,
        order=slot,
        activity_type='other',
    )
    return render(request, 'activities/_ca_row.html', {
        'activity': activity,
        'ca_type_choices': CommonAppActivity.ACTIVITY_TYPE_CHOICES,
        'editing': field,
        'slot_num': slot,
    })


@require_POST
def ca_reorder(request):
    applicant = Applicant.objects.get(pk=1)
    data = json.loads(request.body)
    for i, pk in enumerate(data.get('order', []), start=1):
        CommonAppActivity.objects.filter(pk=pk, applicant=applicant).update(order=i)
    return HttpResponse(status=204)


@require_POST
def ca_delete(request, pk):
    get_object_or_404(CommonAppActivity, pk=pk).delete()
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    return redirect('activities:home_common')


# ── Common App Honor CRUD ──

def honor_add(request):
    if request.method == 'POST' and request.headers.get('HX-Request'):
        applicant = Applicant.objects.get(pk=1)
        honor = CommonAppHonor.objects.create(
            applicant=applicant,
            order=CommonAppHonor.objects.filter(applicant=applicant).count(),
        )
        return render(request, 'activities/_honor_row.html', {'honor': honor})
    if request.method == 'POST':
        form = CommonAppHonorForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.order = CommonAppHonor.objects.count()
            entry.save()
            return redirect('activities:home_common')
    else:
        form = CommonAppHonorForm()
    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': 'Add Common App Honor',
        'back_href': reverse('activities:home_common'), 'back_tab': 'honors',
        'char_fields': {},
    })


def honor_edit(request, pk):
    entry = get_object_or_404(CommonAppHonor, pk=pk)
    if request.method == 'POST':
        form = CommonAppHonorForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('activities:home_common')
    else:
        form = CommonAppHonorForm(instance=entry)

    linked = _get_cross_links(entry.core_activity, 'honor', entry.pk)

    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': f'Edit Honor: {entry.title}',
        'back_href': reverse('activities:home_common'), 'back_tab': 'honors',
        'entry': entry, 'linked': linked,
        'char_fields': {},
    })


def honor_cell(request, pk, field):
    honor = get_object_or_404(CommonAppHonor, pk=pk)
    ctx = {'honor': honor}
    if request.method == 'POST':
        if field in ('title', 'personal_notes'):
            setattr(honor, field, request.POST.get('value', ''))
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
    return redirect('activities:home_common')


# ── MIT Entry CRUD ──

def mit_add(request):
    if request.method == 'POST':
        form = MITEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.order = MITEntry.objects.filter(category=entry.category).count()
            entry.save()
            return redirect('activities:home_mit')
    else:
        form = MITEntryForm()
    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': 'Add MIT Entry',
        'back_href': reverse('activities:home_mit'), 'back_tab': 'mit',
        'char_fields': {},
        'word_fields': {'description': 40},
    })


def mit_edit(request, pk):
    entry = get_object_or_404(MITEntry, pk=pk)
    if request.method == 'POST':
        form = MITEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            return redirect('activities:home_mit')
    else:
        form = MITEntryForm(instance=entry)

    linked = _get_cross_links(entry.core_activity, 'mit', entry.pk)

    return render(request, 'activities/entry_form.html', {
        'form': form, 'title': f'Edit MIT: {entry.org_name}',
        'back_href': reverse('activities:home_mit'), 'back_tab': 'mit',
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
    return redirect('activities:home_mit')


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
        row = [
            f'Entry {i} of {entries.count()}: {e.name}',
            f'Category: {e.get_category_display()}',
            f'Grades: {_grades(e)}',
        ]
        if e.category != 'award':
            row.append(f'Hours/week: {e.hours_per_week or "—"}    Weeks/year: {e.weeks_per_year or "—"}')
        if e.category in ('award', 'volunteer', 'work'):
            row += [
                f'Background ({len(e.background)}/250 chars):',
                f'  {e.background or "(empty)"}',
            ]
        row += [
            f'Description ({len(e.description)}/350 chars):',
            f'  {e.description or "(empty)"}',
        ]
        if e.category == 'award':
            levels = [label for val, label in [
                (e.level_school, 'School'), (e.level_city, 'City'),
                (e.level_state, 'State'), (e.level_regional, 'Regional'),
                (e.level_national, 'National'), (e.level_international, 'International'),
            ] if val]
            row.append(f'Level(s) of Recognition: {", ".join(levels) or "—"}')
            academic = 'Yes' if e.is_academic else ('No' if e.is_academic is False else '—')
            row.append(f'Academic: {academic}')
        if e.category == 'work':
            still = 'Yes' if e.still_working else ('No' if e.still_working is False else '—')
            row.append(f'Still working there: {still}')
        if e.personal_notes:
            row.append(f'Private notes: {e.personal_notes}')
        lines += row + ['', '-' * 40, '']
    content = '\n'.join(lines)
    content += '\n\nJacob thinks this could be formatted better but hasn\'t put effort into reformatting it. It would take like 2 minutes with claude so please email him at chromaticconflux@gmail.com if it should be reformatted for easier copy-pasting'
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="uc_activities.txt"'
    return response


def export_uc_csv(request):
    applicant = Applicant.objects.get(pk=1)
    entries = UCEntry.objects.filter(applicant=applicant).order_by('order')

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        'Name', 'Category', 'Background (250ch)', 'Description (350ch)',
        'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12',
        'Hrs/wk', 'Wks/yr',
        'Level: School', 'Level: City', 'Level: State',
        'Level: Regional', 'Level: National', 'Level: International',
        'Academic?', 'Still work?', 'Private Notes',
    ])
    for e in entries:
        academic = 'Yes' if e.is_academic else ('No' if e.is_academic is False else '')
        still = 'Yes' if e.still_working else ('No' if e.still_working is False else '')
        writer.writerow([
            e.name,
            e.get_category_display(),
            e.background,
            e.description,
            'Yes' if e.grade_9 else '',
            'Yes' if e.grade_10 else '',
            'Yes' if e.grade_11 else '',
            'Yes' if e.grade_12 else '',
            e.hours_per_week,
            e.weeks_per_year,
            'Yes' if e.level_school else '',
            'Yes' if e.level_city else '',
            'Yes' if e.level_state else '',
            'Yes' if e.level_regional else '',
            'Yes' if e.level_national else '',
            'Yes' if e.level_international else '',
            academic,
            still,
            e.personal_notes,
        ])

    response = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="uc_activities.csv"'
    return response


def export_ca_txt(request):
    applicant = Applicant.objects.get(pk=1)
    activities = CommonAppActivity.objects.filter(applicant=applicant).order_by('order')
    lines = [f'COMMON APP ACTIVITIES ({activities.count()}/10)', '=' * 40, '']
    for i, a in enumerate(activities, 1):
        timing = []
        if a.timing_school: timing.append('During school year')
        if a.timing_breaks: timing.append('School breaks')
        if a.timing_all_year: timing.append('All year')
        similar = 'Yes' if a.similar_in_college else ('No' if a.similar_in_college is False else '—')
        lines += [
            f'Activity {i}: {a.organization or "(no org)"}',
            f'Type: {a.get_activity_type_display()}',
            f'Position/Leadership ({len(a.position)}/50 chars): {a.position or "—"}',
            f'Organization ({len(a.organization)}/100 chars): {a.organization or "—"}',
            f'Grades: {_grades(a)}',
            f'Timing: {", ".join(timing) or "—"}',
            f'Hours/week: {a.hours_per_week or "—"}    Weeks/year: {a.weeks_per_year or "—"}',
            f'Continuing in college: {similar}',
            f'Description ({len(a.description)}/150 chars):',
            f'  {a.description or "(empty)"}',
            '',
            '-' * 40,
            '',
        ]
        if a.personal_notes:
            lines.insert(-1, f'Private notes: {a.personal_notes}')
    content = '\n'.join(lines)
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="ca_activities.txt"'
    return response


def export_ca_csv(request):
    applicant = Applicant.objects.get(pk=1)
    activities = CommonAppActivity.objects.filter(applicant=applicant).order_by('order')
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        '#', 'Type', 'Position (50ch)', 'Organization (100ch)', 'Description (150ch)',
        'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12',
        'Timing: School yr', 'Timing: Breaks', 'Timing: All year',
        'Hrs/wk', 'Wks/yr', 'Continuing in college?', 'Private Notes',
    ])
    for i, a in enumerate(activities, 1):
        similar = 'Yes' if a.similar_in_college else ('No' if a.similar_in_college is False else '')
        writer.writerow([
            i,
            a.get_activity_type_display(),
            a.position,
            a.organization,
            a.description,
            'Yes' if a.grade_9 else '',
            'Yes' if a.grade_10 else '',
            'Yes' if a.grade_11 else '',
            'Yes' if a.grade_12 else '',
            'Yes' if a.timing_school else '',
            'Yes' if a.timing_breaks else '',
            'Yes' if a.timing_all_year else '',
            a.hours_per_week or '',
            a.weeks_per_year or '',
            similar,
            a.personal_notes,
        ])
    response = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="ca_activities.csv"'
    return response


def export_honors_txt(request):
    applicant = Applicant.objects.get(pk=1)
    honors = CommonAppHonor.objects.filter(applicant=applicant).order_by('order')
    lines = [f'COMMON APP HONORS ({honors.count()}/5)', '=' * 40, '']
    for i, h in enumerate(honors, 1):
        levels = []
        if h.level_school: levels.append('School')
        if h.level_state_regional: levels.append('State/Regional')
        if h.level_national: levels.append('National')
        if h.level_international: levels.append('International')
        lines += [
            f'Honor {i}: {h.title or "(untitled)"}',
            f'Grades: {_grades(h)}',
            f'Recognition Level: {", ".join(levels) or "—"}',
        ]
        if h.personal_notes:
            lines.append(f'Private notes: {h.personal_notes}')
        lines += ['', '-' * 40, '']
    content = '\n'.join(lines)
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="ca_honors.txt"'
    return response


def export_honors_csv(request):
    applicant = Applicant.objects.get(pk=1)
    honors = CommonAppHonor.objects.filter(applicant=applicant).order_by('order')
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        '#', 'Title', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12',
        'Level: School', 'Level: State/Regional', 'Level: National', 'Level: International',
        'Private Notes',
    ])
    for i, h in enumerate(honors, 1):
        writer.writerow([
            i,
            h.title,
            'Yes' if h.grade_9 else '',
            'Yes' if h.grade_10 else '',
            'Yes' if h.grade_11 else '',
            'Yes' if h.grade_12 else '',
            'Yes' if h.level_school else '',
            'Yes' if h.level_state_regional else '',
            'Yes' if h.level_national else '',
            'Yes' if h.level_international else '',
            h.personal_notes,
        ])
    response = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="ca_honors.csv"'
    return response


# Keep old combined export for backwards compatibility / direct links
def export_common_app(request):
    return export_ca_txt(request)


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
    content += '\n\nJacob thinks this could be formatted better but hasn\'t put effort into reformatting it. It would take like 2 minutes with claude so please email him at chromaticconflux@gmail.com if it should be reformatted for easier copy-pasting'
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="mit_entries.txt"'
    return response
