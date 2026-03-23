from django.shortcuts import render


def estimator(request):
    return render(request, 'widgets/estimator.html')


def focus_write(request):
    return render(request, 'widgets/focus_write.html')


def word_counter(request):
    return render(request, 'widgets/word_counter.html')
