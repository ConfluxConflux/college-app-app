from django.shortcuts import render

from colleges.models import College
from activities.models import UCEntry, CommonAppActivity, CommonAppHonor, MITEntry
from supplements.models import SupplementEssay


def home(request):
    context = {
        'college_count': College.objects.count(),
        'applying_count': College.objects.exclude(apply_status__in=['', 'not_applying', 'unlikely']).count(),
        'uc_count': UCEntry.objects.count(),
        'common_app_activity_count': CommonAppActivity.objects.count(),
        'common_app_honor_count': CommonAppHonor.objects.count(),
        'mit_count': MITEntry.objects.count(),
        'essay_count': SupplementEssay.objects.count(),
        'essay_done_count': SupplementEssay.objects.filter(status='done').count(),
    }
    return render(request, 'core/home.html', context)
