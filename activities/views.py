from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import UCEntryForm, CommonAppActivityForm, CommonAppHonorForm, MITEntryForm
from .models import UCEntry, CommonAppActivity, CommonAppHonor, MITEntry


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


def activities_home(request):
    tab = request.GET.get('tab', 'uc')
    context = {
        'tab': tab,
        'uc_entries': UCEntry.objects.select_related('core_activity').all(),
        'uc_count': UCEntry.objects.count(),
        'common_app_activities': CommonAppActivity.objects.select_related('core_activity').all(),
        'ca_count': CommonAppActivity.objects.count(),
        'common_app_honors': CommonAppHonor.objects.select_related('core_activity').all(),
        'honor_count': CommonAppHonor.objects.count(),
        'mit_entries': MITEntry.objects.select_related('core_activity').all(),
        'mit_count': MITEntry.objects.count(),
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


@require_POST
def mit_delete(request, pk):
    get_object_or_404(MITEntry, pk=pk).delete()
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    return redirect('/activities/?tab=mit')
