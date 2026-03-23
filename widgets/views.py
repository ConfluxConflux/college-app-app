from django.shortcuts import render


def estimator(request):
    return render(request, 'widgets/estimator.html')


def focus_write(request):
    return render(request, 'widgets/focus_write.html')
