from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from .models import EssayCategory, SupplementEssay


def supplements_home(request):
    context = {
        'categories': EssayCategory.objects.all(),
        'essays': SupplementEssay.objects.select_related('college', 'category').all(),
    }
    return render(request, 'supplements/home.html', context)


@require_POST
def essay_status_edit(request, pk):
    essay = get_object_or_404(SupplementEssay, pk=pk)
    status = request.POST.get('status', '')
    valid_statuses = {v for v, _ in SupplementEssay.STATUS_CHOICES}
    if status in valid_statuses:
        essay.status = status
        essay.save()
    return HttpResponse(status=204)
