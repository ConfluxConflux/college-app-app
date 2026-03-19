from .models import Applicant


def applicant(request):
    """Inject the current applicant into every template context.
    Swap this for request.user.applicant once real auth exists."""
    try:
        return {'applicant': Applicant.objects.get(pk=1)}
    except Applicant.DoesNotExist:
        return {'applicant': None}
