from collections import defaultdict

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST, require_http_methods

from colleges.models import College
from .models import EssayCategory, SupplementEssay


def _augment_essays(essays):
    """Attach progress_pct, limit_display, count_display, limit_type, limit_val."""
    for e in essays:
        if e.word_limit and e.word_limit > 0:
            e.progress_pct = min(int(e.word_count / e.word_limit * 100), 100)
            e.limit_display = f'{e.word_limit}w'
            e.count_display = f'{e.word_count}/{e.word_limit}'
            e.limit_type = 'word'
            e.limit_val = e.word_limit
        elif e.char_limit and e.char_limit > 0:
            e.progress_pct = min(int(e.char_count / e.char_limit * 100), 100)
            e.limit_display = f'{e.char_limit}ch'
            e.count_display = f'{e.char_count}/{e.char_limit}'
            e.limit_type = 'char'
            e.limit_val = e.char_limit
        else:
            e.progress_pct = 0
            e.limit_display = ''
            e.count_display = str(e.word_count) if e.response else ''
            e.limit_type = 'word'
            e.limit_val = 0


def supplements_home(request):
    all_essays = list(
        SupplementEssay.objects.select_related('college', 'category').order_by('sort_order')
    )
    _augment_essays(all_essays)

    # By College: restore selected college from GET param
    selected_college_pk = request.GET.get('college')
    selected_college = None
    college_essays = []
    if selected_college_pk:
        try:
            selected_college = College.objects.get(pk=int(selected_college_pk))
            college_essays = [e for e in all_essays if e.college_id == selected_college.pk]
        except (College.DoesNotExist, ValueError):
            pass

    # Matrix: colleges and categories that have at least one essay
    essay_map = defaultdict(list)
    for e in all_essays:
        essay_map[(e.college_id, e.category_id)].append(e)

    matrix_colleges = list(
        College.objects.filter(essays__isnull=False).distinct().order_by('name')
    )
    categories = list(
        EssayCategory.objects.filter(essays__isnull=False).distinct()
    )

    matrix_rows = []
    for cat in categories:
        cells = []
        has_any = False
        for college in matrix_colleges:
            cell_essays = essay_map.get((college.pk, cat.pk), [])
            cells.append({'college': college, 'essays': cell_essays})
            if cell_essays:
                has_any = True
        if has_any:
            matrix_rows.append({'category': cat, 'cells': cells})

    by_college_list = [
        {'college': c, 'essays': [e for e in all_essays if e.college_id == c.pk]}
        for c in matrix_colleges
    ]

    context = {
        'all_essays': all_essays,
        'matrix_colleges': matrix_colleges,
        'matrix_rows': matrix_rows,
        'by_college_list': by_college_list,
        'selected_college': selected_college,
        'all_categories': EssayCategory.objects.all(),
        'status_choices': SupplementEssay.STATUS_CHOICES,
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


@require_http_methods(['POST'])
def essay_save(request, pk):
    essay = get_object_or_404(SupplementEssay, pk=pk)
    response = request.POST.get('response', '')
    essay.response = response
    essay.save()
    wc = len(response.split()) if response.strip() else 0
    cc = len(response)
    return JsonResponse({'word_count': wc, 'char_count': cc})


@require_http_methods(['POST'])
def essay_category_edit(request, pk):
    essay = get_object_or_404(SupplementEssay, pk=pk)
    cat_pk = request.POST.get('category', '')
    if cat_pk == '':
        essay.category = None
        essay.save()
    else:
        try:
            cat = EssayCategory.objects.get(pk=int(cat_pk))
            essay.category = cat
            essay.save()
        except (EssayCategory.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Invalid category'}, status=400)
    return HttpResponse(status=204)


def essay_focus(request, pk):
    essay = get_object_or_404(SupplementEssay, pk=pk)
    _augment_essays([essay])
    return render(request, 'supplements/focus.html', {'essay': essay})
