from .models import Applicant


def applicant(request):
    if not request.user.is_authenticated:
        return {'applicant': None}
    try:
        return {'applicant': request.user.applicant}
    except Applicant.DoesNotExist:
        return {'applicant': None}
