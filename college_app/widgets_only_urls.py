"""Root URLconf for the widgets-only build (WIDGETS_ONLY=True).

Deliberately tiny: only the widget pages exist. No admin, no allauth, no
colleges/activities/essays/dashboard. Anything else 404s, so there is no way
to stumble into the half-finished parts of the tracker from here.

The widgets sit at short top-level paths (see widgets/urls_standalone.py).
The old /widgets/... paths redirect there, so links shared before the move
still work.
"""
from django.urls import include, path
from django.views.generic import RedirectView

from widgets import views as widget_views

_LEGACY = {
    'widgets/': '/words',
    'widgets/word-counter/': '/words',
    'widgets/focus-write/': '/focus',
    'widgets/pomodoros/': '/pomos',
    'widgets/time-calculator/': '/time',
    'widgets/advice/': '/advice',
    'widgets/resources/': '/resources',
}

urlpatterns = [
    path('', widget_views.welcome, name='welcome'),
    path('', include('widgets.urls_standalone')),
]

urlpatterns += [
    path(old, RedirectView.as_view(url=new, permanent=False, query_string=True))
    for old, new in _LEGACY.items()
]

urlpatterns += [
    # Not a redirect: a 302 would drop the POST body from an older page.
    path('widgets/scratchpad/<slug:slot>/save/', widget_views.scratchpad_save),
]
