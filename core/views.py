from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from colleges.models import College
from activities.models import UCEntry, CommonAppActivity, CommonAppHonor, MITEntry
from supplements.models import SupplementEssay
from .models import Applicant, CoreActivity


# Temporary: test applicant switcher until real auth is wired up.
# When auth exists, replace with: applicant = request.user.applicant
def _get_applicant(request):
    from .utils import get_applicant
    return get_applicant(request)


def switch_applicant(request, pk):
    request.session['applicant_pk'] = pk
    return redirect('core:home')


def _core_row_ctx(activity, editing=None):
    """Full context needed to render one row of the Centralized table."""
    return {
        'activity': activity,
        'uc_entry': activity.uc_entries.first(),
        'ca_entry': activity.common_app_activities.first(),
        'honor_entry': activity.common_app_honors.first(),
        'mit_entry': activity.mit_entries.first(),
        'uc_category_choices': UCEntry.CATEGORY_CHOICES,
        'ca_type_choices': CommonAppActivity.ACTIVITY_TYPE_CHOICES,
        'mit_category_choices': MITEntry.CATEGORY_CHOICES,
        'editing': editing,
    }


def landing(request):
    return render(request, 'core/landing.html')


def not_yet(request):
    return render(request, 'core/not_yet.html')


def profile(request):
    applicant = _get_applicant(request)
    if request.method == 'POST':
        applicant.brainstorm = request.POST.get('brainstorm', '')
        applicant.save()
    return render(request, 'core/profile.html', {'applicant': applicant})



# ── CoreActivity cell editing ──

CORE_TEXT_FIELDS = {'name', 'full_description', 'personal_notes', 'hours_per_week', 'weeks_per_year'}


def core_activity_cell(request, pk, field):
    activity = get_object_or_404(CoreActivity, pk=pk)
    if request.method == 'POST':
        if field in CORE_TEXT_FIELDS:
            setattr(activity, field, request.POST.get('value', ''))
            activity.save()
        elif field == 'grades':
            activity.grade_9 = 'grade_9' in request.POST
            activity.grade_10 = 'grade_10' in request.POST
            activity.grade_11 = 'grade_11' in request.POST
            activity.grade_12 = 'grade_12' in request.POST
            activity.save()
        return render(request, 'core/_core_activity_row.html', _core_row_ctx(activity))
    return render(request, 'core/_core_activity_row.html', _core_row_ctx(activity, editing=field))


def core_activity_add(request):
    applicant = _get_applicant(request)
    activity = CoreActivity.objects.create(
        applicant=applicant,
        name='',
        order=CoreActivity.objects.filter(applicant=applicant).count(),
    )
    return render(request, 'core/_core_activity_row.html', _core_row_ctx(activity, editing='name'))


@require_POST
def core_activity_delete(request, pk):
    get_object_or_404(CoreActivity, pk=pk).delete()
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    return redirect('activities:home')


# ── Format-specific cell editing (get-or-create linked entry) ──

def core_activity_uc_cell(request, pk, field):
    activity = get_object_or_404(CoreActivity, pk=pk)
    uc = activity.uc_entries.first()
    if request.method == 'POST':
        if uc is None:
            uc = UCEntry.objects.create(
                applicant=activity.applicant, core_activity=activity,
                name=activity.name or 'New entry', category='extracurricular',
                order=UCEntry.objects.filter(applicant=activity.applicant).count(),
            )
        if field in ('background', 'description', 'hours_per_week', 'weeks_per_year'):
            setattr(uc, field, request.POST.get('value', ''))
            uc.save()
        elif field == 'category':
            uc.category = request.POST.get('value', '')
            uc.save()
        return render(request, 'core/_core_activity_row.html', _core_row_ctx(activity))
    return render(request, 'core/_core_activity_row.html', _core_row_ctx(activity, editing=f'uc_{field}'))


def core_activity_ca_cell(request, pk, field):
    activity = get_object_or_404(CoreActivity, pk=pk)
    ca = activity.common_app_activities.first()
    if request.method == 'POST':
        if ca is None:
            ca = CommonAppActivity.objects.create(
                applicant=activity.applicant, core_activity=activity,
                activity_type='other',
                order=CommonAppActivity.objects.filter(applicant=activity.applicant).count(),
            )
        if field in ('position', 'organization', 'description'):
            setattr(ca, field, request.POST.get('value', ''))
            ca.save()
        elif field == 'activity_type':
            ca.activity_type = request.POST.get('value', '')
            ca.save()
        return render(request, 'core/_core_activity_row.html', _core_row_ctx(activity))
    return render(request, 'core/_core_activity_row.html', _core_row_ctx(activity, editing=f'ca_{field}'))


def core_activity_honor_cell(request, pk, field):
    activity = get_object_or_404(CoreActivity, pk=pk)
    honor = activity.common_app_honors.first()
    if request.method == 'POST':
        if honor is None:
            honor = CommonAppHonor.objects.create(
                applicant=activity.applicant, core_activity=activity,
                title=activity.name or 'New honor',
                order=CommonAppHonor.objects.filter(applicant=activity.applicant).count(),
            )
        if field == 'title':
            honor.title = request.POST.get('value', '')
            honor.save()
        elif field == 'levels':
            honor.level_school = 'level_school' in request.POST
            honor.level_state_regional = 'level_state_regional' in request.POST
            honor.level_national = 'level_national' in request.POST
            honor.level_international = 'level_international' in request.POST
            honor.save()
        return render(request, 'core/_core_activity_row.html', _core_row_ctx(activity))
    return render(request, 'core/_core_activity_row.html', _core_row_ctx(activity, editing=f'honor_{field}'))


def core_activity_mit_cell(request, pk, field):
    activity = get_object_or_404(CoreActivity, pk=pk)
    mit = activity.mit_entries.first()
    if request.method == 'POST':
        if mit is None:
            mit = MITEntry.objects.create(
                applicant=activity.applicant, core_activity=activity,
                category='activity',
                order=MITEntry.objects.filter(applicant=activity.applicant).count(),
            )
        if field in ('org_name', 'role_award', 'participation_period', 'description'):
            setattr(mit, field, request.POST.get('value', ''))
            mit.save()
        elif field == 'category':
            mit.category = request.POST.get('value', '')
            mit.save()
        return render(request, 'core/_core_activity_row.html', _core_row_ctx(activity))
    return render(request, 'core/_core_activity_row.html', _core_row_ctx(activity, editing=f'mit_{field}'))


def home(request):
    applicant = _get_applicant(request)
    college_count = College.objects.filter(applicant=applicant).count()
    applying_count = College.objects.filter(applicant=applicant).exclude(apply_status__in=['', 'not_applying', 'unlikely']).count()
    uc_count = UCEntry.objects.filter(applicant=applicant).count()
    common_app_activity_count = CommonAppActivity.objects.filter(applicant=applicant).count()
    common_app_honor_count = CommonAppHonor.objects.filter(applicant=applicant).count()
    mit_count = MITEntry.objects.filter(applicant=applicant).count()
    essay_count = SupplementEssay.objects.filter(applicant=applicant).count()
    essay_done_count = SupplementEssay.objects.filter(applicant=applicant, status='done').count()
    submitted_count = College.objects.filter(applicant=applicant, apply_status__in=['applied', 'accepted', 'deferred', 'waitlisted', 'rejected', 'enrolled', 'withdrawn']).count()
    context = {
        'applicant': applicant,
        'college_count': college_count,
        'applying_count': applying_count,
        'uc_count': uc_count,
        'common_app_activity_count': common_app_activity_count,
        'common_app_honor_count': common_app_honor_count,
        'mit_count': mit_count,
        'essay_count': essay_count,
        'essay_done_count': essay_done_count,
        'submitted_count': submitted_count,
        # Auto-detection flags for the dashboard checklist
        'auto_has_college_list': college_count >= 4,
        'auto_has_big_college_list': college_count >= 8,
        'auto_has_activities': uc_count > 0 or common_app_activity_count > 0,
        'auto_has_essay': essay_count > 0,
        'auto_has_done_essay': essay_done_count > 0,
        'auto_has_submitted': submitted_count > 0,
    }
    return render(request, 'core/home.html', context)
