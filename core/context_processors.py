from django.conf import settings

from .models import Applicant


def applicant(request):
    # `debug` gates dev-only UI (the applicant switcher). Django's own debug
    # context processor only fires for INTERNAL_IPS, which Railway never
    # matches, so expose the flag directly.
    ctx = {'debug': settings.DEBUG}
    if not request.user.is_authenticated:
        ctx['applicant'] = None
        return ctx
    try:
        ctx['applicant'] = request.user.applicant
    except Applicant.DoesNotExist:
        ctx['applicant'] = None
    return ctx
