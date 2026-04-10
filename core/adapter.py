from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.http import HttpResponseRedirect


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if not sociallogin.is_existing:
            request.session['socialaccount_sociallogin'] = sociallogin.serialize()
            raise ImmediateHttpResponse(HttpResponseRedirect('/are-you-sure'))
