from django.shortcuts import redirect


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
            if path not in self.EXEMPT_EXACT and not path.startswith('/accounts/') and not path.startswith('/admin/'):
                return redirect(f'/accounts/login/?next={path}')
        return self.get_response(request)
