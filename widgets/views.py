from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from core.models import Applicant


def _current_applicant(request):
    """The logged-in user's Applicant, or None (widgets are usable logged-out)."""
    if not request.user.is_authenticated:
        return None
    try:
        return request.user.applicant
    except Applicant.DoesNotExist:
        return None


def estimator(request):
    return render(request, 'widgets/estimator.html')


def focus_write(request):
    applicant = _current_applicant(request)
    return render(request, 'widgets/focus_write.html', {
        'draft': applicant.focus_draft if applicant else '',
        'can_save': applicant is not None,
    })


@require_POST
def focus_write_save(request):
    """Persist the shared Focus Write scratchpad. Logged-out visitors get a no-op
    (the page keeps their text in localStorage instead)."""
    applicant = _current_applicant(request)
    if applicant is None:
        return HttpResponse(status=204)
    applicant.focus_draft = request.POST.get('text', '')
    applicant.save(update_fields=['focus_draft'])
    return HttpResponse(status=204)


def timer(request):
    return render(request, 'widgets/timer.html')


def word_counter(request):
    return render(request, 'widgets/word_counter.html')


def resources(request):
    links = [
        {
            'title': "CollegeVine (good for building a list & estimating your chances, but take with salt)",
            'url': 'http://collegevine.com/',
            'source': 'collegevine.com',
        },
        {
            'title': "MIT Admissions Blog (pretty fun I think!)",
            'url': 'https://mitadmissions.org/blogs/',
            'source': 'mitadmissions.org',
        },
        {
            'title': "The Notorious A2C (but don't get sucked down the distraction hole)",
            'url': 'https://www.applyingto.college/home',
            'source': 'applyingto.college',
        },
        {
            'title': "Admissions Matters (supposedly comprehensive book that I've never read)",
            'url': 'https://www.amazon.com/Admission-Matters-Students-Parents-Getting/dp/1119885736/',
            'source': 'amazon.com',
        },
        {
            'title': "3Blue1Brown Soundtrack (my favorite music for focusing)",
            'url': 'https://vincerubinetti.bandcamp.com/album/the-music-of-3blue1brown',
            'source': 'vincerubinetti.bandcamp.com',
        },
    ]
    return render(request, 'widgets/resources.html', {'links': links})


def advice(request):
    links = [
        {
            'title': "Jacob's College Application FAQ",
            'url': 'https://beautifulthorns.wixsite.com/home/post/jacob-s-college-application-faq-wip-week',
            'source': 'beautifulthorns.wixsite.com',
        },
        {
            'title': "Applying Sideways",
            'url': 'https://mitadmissions.org/blogs/entry/applying_sideways/',
            'source': 'mitadmissions.org',
        },
        {
            'title': "College advice for people who are exactly like me",
            'url': 'https://www.benkuhn.net/college/',
            'source': 'benkuhn.net',
        },
        {
            'title': "Thoughts about College Admissions",
            'url': 'https://docs.google.com/document/d/1FPAK8zeqHCmVRaXMxDT-ylCUug04YqhS6Lf9ypynP5g/edit?tab=t.0',
            'source': 'docs.google.com',
        },
        {
            'title': "Writing, Briefly",
            'url': 'https://paulgraham.com/writing44.html',
            'source': 'paulgraham.com',
        },
    ]
    return render(request, 'widgets/advice.html', {'links': links})
