from django.dispatch import receiver
from allauth.account.signals import user_signed_up, user_logged_in


@receiver(user_signed_up)
def create_applicant_for_new_user(request, user, **kwargs):
    from .models import Applicant

    first_name = ''
    last_name = ''
    picture_url = ''

    sociallogin = kwargs.get('sociallogin')
    if sociallogin:
        extra = sociallogin.account.extra_data
        first_name = extra.get('given_name', '')
        last_name = extra.get('family_name', '')
        picture_url = extra.get('picture', '')
        if not first_name and extra.get('name'):
            parts = extra['name'].split()
            first_name = parts[0]
            last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''

    if not first_name:
        first_name = user.first_name or ''
    if not last_name:
        last_name = user.last_name or ''

    Applicant.objects.create(
        user=user,
        first_name=first_name,
        last_name=last_name,
        email=user.email or '',
        profile_picture=picture_url,
    )


@receiver(user_logged_in)
def sync_profile_picture(request, user, **kwargs):
    """Keep profile picture in sync with Google on each login."""
    try:
        social = user.socialaccount_set.filter(provider='google').first()
        if not social:
            return
        picture_url = social.extra_data.get('picture', '')
        if picture_url:
            applicant = user.applicant
            if applicant.profile_picture != picture_url:
                applicant.profile_picture = picture_url
                applicant.save(update_fields=['profile_picture'])
    except Exception:
        pass
