from django.shortcuts import render


def estimator(request):
    return render(request, 'widgets/estimator.html')
