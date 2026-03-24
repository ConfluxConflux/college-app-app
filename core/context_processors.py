from .utils import get_applicant


def applicant(request):
    """Inject the current applicant into every template context.
    Swap this for request.user.applicant once real auth exists."""
    try:
        return {'applicant': get_applicant(request)}
    except Exception:
        return {'applicant': None}
