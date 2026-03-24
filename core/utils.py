from .models import Applicant


def get_applicant(request):
    pk = request.session.get('applicant_pk', 1)
    return Applicant.objects.get(pk=pk)
