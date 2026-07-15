from collections import defaultdict

from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

from colleges.models import UserCollege
from .models import (
    EssayCategory,
    EssayPrompt,
    SupplementEssay,
    UCPersonalInsightQuestion,
    CommonAppEssay,
    ensure_default_tags,
)


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
    applicant = request.user.applicant
    ensure_default_tags(applicant)
    all_essays = list(
        SupplementEssay.objects.filter(applicant=applicant)
        .select_related('college', 'category', 'selected_prompt')
        # The cards read prompts for the choice picker; without this that is a
        # query per essay.
        .prefetch_related('prompts')
        .order_by('sort_order')
    )
    _augment_essays(all_essays)

    # By College: restore selected college from GET param
    selected_college_pk = request.GET.get('college')
    selected_college = None
    college_essays = []
    if selected_college_pk:
        try:
            selected_college = UserCollege.objects.get(pk=int(selected_college_pk), applicant=applicant)
            college_essays = [e for e in all_essays if e.college_id == selected_college.pk]
        except (UserCollege.DoesNotExist, ValueError):
            pass

    # Matrix: colleges and categories that have at least one essay
    essay_map = defaultdict(list)
    for e in all_essays:
        essay_map[(e.college_id, e.category_id)].append(e)

    matrix_colleges = list(
        UserCollege.objects.filter(essays__applicant=applicant).distinct().order_by('college__name')
    )
    categories = list(
        EssayCategory.objects.filter(applicant=applicant, essays__isnull=False).distinct()
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
        if not has_any:
            continue

        # The reuse signal: a tag used by more than one college is the same
        # question asked twice. Kathy's redundancy problem, for essays.
        row_essays = [e for c in cells for e in c['essays']]
        colleges_asking = sum(1 for c in cells if c['essays'])
        limits = sorted({e.word_limit for e in row_essays if e.word_limit})
        written = [e for e in row_essays if e.response.strip()]

        matrix_rows.append({
            'category': cat,
            'cells': cells,
            'colleges_asking': colleges_asking,
            'is_reusable': colleges_asking > 1,
            # Reuse is only realistic if the lengths are close. Two 250-word
            # prompts are one essay; 100 and 650 are not.
            'limit_range': (limits[0], limits[-1]) if len(limits) > 1 else None,
            'limits_compatible': (
                len(limits) > 1 and limits[-1] <= limits[0] * 2
            ) if limits else False,
            'written_count': len(written),
            'longest_written': max(written, key=lambda e: e.word_count) if written else None,
        })

    # Most-shared tags first: those are where the reuse is.
    matrix_rows.sort(key=lambda r: (-r['colleges_asking'], r['category'].sort_order))

    by_college_list = [
        {'college': c, 'essays': [e for e in all_essays if e.college_id == c.pk]}
        for c in matrix_colleges
    ]

    # Every college on the list, not just ones that already have essays —
    # otherwise you could never add the first essay for a school.
    addable_colleges = [
        c for c in UserCollege.objects.filter(applicant=applicant)
                                      .exclude(apply_status='not_applying')
                                      .select_related('college')
    ]
    addable_colleges.sort(key=lambda c: (c.name or '').lower())

    context = {
        'all_essays': all_essays,
        'matrix_colleges': matrix_colleges,
        'matrix_rows': matrix_rows,
        'by_college_list': by_college_list,
        'selected_college': selected_college,
        'addable_colleges': addable_colleges,
        'all_categories': EssayCategory.objects.filter(applicant=applicant),
        'status_choices': SupplementEssay.STATUS_CHOICES,
    }
    return render(request, 'supplements/home.html', context)


@require_POST
def essay_status_edit(request, pk):
    essay = get_object_or_404(SupplementEssay, pk=pk, applicant=request.user.applicant)
    status = request.POST.get('status', '')
    valid_statuses = {v for v, _ in SupplementEssay.STATUS_CHOICES}
    if status in valid_statuses:
        essay.status = status
        essay.save()
    return HttpResponse(status=204)


@require_http_methods(['POST'])
def essay_save(request, pk):
    essay = get_object_or_404(SupplementEssay, pk=pk, applicant=request.user.applicant)
    response = request.POST.get('response', '')
    essay.response = response
    essay.save()
    wc = len(response.split()) if response.strip() else 0
    cc = len(response)
    return JsonResponse({'word_count': wc, 'char_count': cc})


@require_http_methods(['POST'])
def essay_category_edit(request, pk):
    essay = get_object_or_404(SupplementEssay, pk=pk, applicant=request.user.applicant)
    cat_pk = request.POST.get('category', '')
    if cat_pk == '':
        essay.category = None
        essay.save()
    else:
        try:
            # Scoped to the applicant: tags are owned now, and an unscoped
            # lookup would let one applicant tag an essay with another's tag.
            cat = EssayCategory.objects.get(pk=int(cat_pk), applicant=request.user.applicant)
            essay.category = cat
            essay.save()
        except (EssayCategory.DoesNotExist, ValueError):
            return JsonResponse({'error': 'Invalid category'}, status=400)
    return HttpResponse(status=204)


@require_POST
def essay_create(request):
    """Add an essay to one of the applicant's colleges.

    Hippocampus does not presuppose that any college asks any particular
    essay — the applicant says what the college wants. A prompt is required
    because an essay without one is just a text box; everything else can be
    filled in later.
    """
    applicant = request.user.applicant

    college = get_object_or_404(
        UserCollege, pk=request.POST.get('college') or 0, applicant=applicant
    )

    # One or more prompt options; blanks are dropped so a stray empty box in
    # the form doesn't become an empty choice.
    prompt_texts = [p.strip() for p in request.POST.getlist('prompt') if p.strip()]
    if not prompt_texts:
        return HttpResponse('An essay needs at least one prompt', status=400)

    limit_type = request.POST.get('limit_type', 'word')
    try:
        limit = int(request.POST.get('limit') or 0)
    except ValueError:
        limit = 0
    word_limit = limit if (limit > 0 and limit_type == 'word') else None
    char_limit = limit if (limit > 0 and limit_type == 'char') else None

    category = None
    cat_pk = request.POST.get('category') or ''
    if cat_pk:
        category = EssayCategory.objects.filter(pk=cat_pk, applicant=applicant).first()

    status = request.POST.get('status', 'todo')
    if status not in {v for v, _ in SupplementEssay.STATUS_CHOICES}:
        status = 'todo'

    last = SupplementEssay.objects.filter(applicant=applicant).order_by('-sort_order').first()

    with transaction.atomic():
        essay = SupplementEssay.objects.create(
            applicant=applicant,
            college=college,
            category=category,
            prompt=prompt_texts[0],
            word_limit=word_limit,
            char_limit=char_limit,
            status=status,
            sort_order=(last.sort_order + 1) if last else 0,
        )
        prompts = [
            EssayPrompt.objects.create(essay=essay, text=text, sort_order=i)
            for i, text in enumerate(prompt_texts)
        ]
        # A single prompt is not a choice, so pick it. With several, the
        # applicant decides — that is the point of offering them.
        if len(prompts) == 1:
            essay.selected_prompt = prompts[0]
            essay.save(update_fields=['selected_prompt'])

    return redirect(f"{reverse('supplements:home')}?college={college.pk}")


@require_POST
def essay_delete(request, pk):
    """Delete an essay. Its prompts go with it (cascade); nothing else does."""
    essay = get_object_or_404(SupplementEssay, pk=pk, applicant=request.user.applicant)
    college_pk = essay.college_id
    essay.delete()
    if request.headers.get('HX-Request'):
        return HttpResponse('')
    return redirect(f"{reverse('supplements:home')}?college={college_pk}")


@require_POST
def essay_prompt_select(request, pk):
    """Choose which of an essay's prompts it answers."""
    essay = get_object_or_404(SupplementEssay, pk=pk, applicant=request.user.applicant)
    prompt_pk = request.POST.get('prompt') or ''
    if prompt_pk == '':
        essay.selected_prompt = None
    else:
        # Scoped to this essay: another essay's prompt is not an option here.
        prompt = essay.prompts.filter(pk=prompt_pk).first()
        if prompt is None:
            return HttpResponse('That prompt is not one of this essay\'s options', status=400)
        essay.selected_prompt = prompt
    essay.save(update_fields=['selected_prompt'])
    return HttpResponse(status=204)


@require_POST
def tag_create(request):
    """Add a tag of the applicant's own."""
    applicant = request.user.applicant
    name = request.POST.get('name', '').strip()
    if not name:
        return HttpResponse('A name is required', status=400)
    if EssayCategory.objects.filter(applicant=applicant, name__iexact=name).exists():
        return HttpResponse('You already have a tag with that name', status=400)
    last = EssayCategory.objects.filter(applicant=applicant).order_by('-sort_order').first()
    EssayCategory.objects.create(
        applicant=applicant, name=name,
        sort_order=(last.sort_order + 1) if last else 0,
    )
    return render(request, 'supplements/_tag_manager.html', {
        'all_categories': EssayCategory.objects.filter(applicant=applicant),
    })


@require_POST
def tag_delete(request, pk):
    """Delete a tag. Essays keep their text and simply become untagged."""
    applicant = request.user.applicant
    tag = get_object_or_404(EssayCategory, pk=pk, applicant=applicant)
    tag.delete()  # SupplementEssay.category is SET_NULL — no essay is lost
    return render(request, 'supplements/_tag_manager.html', {
        'all_categories': EssayCategory.objects.filter(applicant=applicant),
    })


def essay_focus(request, pk):
    essay = get_object_or_404(SupplementEssay, pk=pk, applicant=request.user.applicant)
    _augment_essays([essay])
    return render(request, 'supplements/focus.html', {'essay': essay})


@require_POST
def uc_piq_status_edit(request, pk):
    piq = get_object_or_404(UCPersonalInsightQuestion, pk=pk, applicant=request.user.applicant)
    status = request.POST.get('status', '')
    if status in {v for v, _ in UCPersonalInsightQuestion.STATUS_CHOICES}:
        piq.status = status
        piq.save()
    return HttpResponse(status=204)


@require_POST
def uc_piq_save(request, pk):
    piq = get_object_or_404(UCPersonalInsightQuestion, pk=pk, applicant=request.user.applicant)
    piq.response = request.POST.get('response', '')
    piq.save()
    return JsonResponse({'word_count': piq.word_count})


@require_POST
def common_essay_status_edit(request, pk):
    essay = get_object_or_404(CommonAppEssay, pk=pk, applicant=request.user.applicant)
    status = request.POST.get('status', '')
    if status in {v for v, _ in CommonAppEssay.STATUS_CHOICES}:
        essay.status = status
        essay.save()
    return HttpResponse(status=204)


@require_POST
def common_essay_save(request, pk):
    essay = get_object_or_404(CommonAppEssay, pk=pk, applicant=request.user.applicant)
    essay.response = request.POST.get('response', '')
    essay.prompt_choice = request.POST.get('prompt_choice') or None
    essay.save()
    return JsonResponse({'word_count': essay.word_count})
