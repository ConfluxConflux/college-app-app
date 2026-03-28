from django.shortcuts import redirect


class WwwRedirectMiddleware:
    """Redirect www.collegeappapp.com → collegeappapp.com (permanent)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        if host.startswith('www.'):
            bare = host[4:]
            return redirect(f'https://{bare}{request.get_full_path()}', permanent=True)
        return self.get_response(request)


class LoginRequiredMiddleware:
    """Redirect unauthenticated users to login for all URLs except the whitelist."""

    EXEMPT_PREFIXES = (
        '/accounts/',   # allauth login/OAuth/signup
        '/admin/',      # Django admin has its own auth
        '/',            # landing page (exact match handled below)
    )
    EXEMPT_EXACT = {'/'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path
            if (path not in self.EXEMPT_EXACT
                    and not path.startswith('/accounts/')
                    and not path.startswith('/admin/')
                    and not path.startswith('/switch-applicant/')
                    and path not in ('/widgets/time-calculator/', '/widgets/word-counter/')):
                return redirect(f'/accounts/login/?next={path}')
        return self.get_response(request)
