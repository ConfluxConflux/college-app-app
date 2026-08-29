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


# Which Applicant field backs each scratchpad slot.
SCRATCHPAD_FIELDS = {'focus': 'focus_draft', 'words': 'word_counter_draft'}


@require_POST
def scratchpad_save(request, slot):
    """Persist a scratchpad (Focus Write / Word Counter) to the account. Logged-out
    visitors get a no-op — the page keeps their text in localStorage instead."""
    field = SCRATCHPAD_FIELDS.get(slot)
    if field is None:
        return HttpResponse(status=404)
    applicant = _current_applicant(request)
    if applicant is None:
        return HttpResponse(status=204)
    setattr(applicant, field, request.POST.get('text', ''))
    applicant.save(update_fields=[field])
    return HttpResponse(status=204)


def welcome(request):
    """Front door of the widgets-only build (its "/"). Not routed in the full
    site, which has its own landing page."""
    return render(request, 'widgets/welcome.html')


def estimator(request):
    return render(request, 'widgets/estimator.html')


def focus_write(request):
    applicant = _current_applicant(request)
    return render(request, 'widgets/focus_write.html', {
        'draft': applicant.focus_draft if applicant else '',
        'can_save': applicant is not None,
    })


def timer(request):
    return render(request, 'widgets/timer.html')


def word_counter(request):
    applicant = _current_applicant(request)
    return render(request, 'widgets/word_counter.html', {
        'draft': applicant.word_counter_draft if applicant else '',
        'can_save': applicant is not None,
    })


def resources(request):
    links = [
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
            'title': "College Essay Advisors (prompt-by-prompt breakdowns for the Common App and supplements)",
            'url': 'https://www.collegeessayadvisors.com/',
            'source': 'collegeessayadvisors.com',
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
