from django.shortcuts import render
from .models import EssayCategory, SupplementEssay


def supplements_home(request):
    context = {
        'categories': EssayCategory.objects.all(),
        'essays': SupplementEssay.objects.select_related('college', 'category').all(),
    }
    return render(request, 'supplements/home.html', context)
