"""Root-level widget URLs for the standalone build (WIDGETS_ONLY=True).

On hippocampus.college the widgets *are* the site, so each one gets a short
top-level path — /words, /focus, /pomos, /time, /advice, /resources — rather
than hiding under /widgets/. These are the canonical routes, so every
{% url 'widgets:...' %} in the shared templates resolves to the short form.

Each canonical path has aliases that redirect to it, including the
trailing-slash form, so a guessed or half-remembered URL still lands.

Redirects are 302 rather than 301 on purpose: a 301 sticks in visitors'
browsers, and these names are new enough to still be worth changing.
"""
from django.conf import settings
from django.urls import path, re_path
from django.views.generic import RedirectView

from . import views

app_name = 'widgets'


def _alias(target):
    """A redirect to one of the canonical paths above."""
    return RedirectView.as_view(url=target, permanent=False, query_string=True)


# canonical path, view, url name, aliases that redirect to it
WIDGETS = [
    ('words',     views.word_counter, 'word_counter', ['word-counter', 'wc']),
    ('focus',     views.focus_write,  'focus_write',  ['focus-write', 'fw']),
    ('pomos',     views.timer,        'timer',        ['pomodoros', 'pomodoro-timer', 'pt', 'timer']),
    ('time',      views.estimator,    'estimator',    ['activity-time-calculator', 'time-calculator']),
    ('advice',    views.advice,       'advice',       []),
    ('resources', views.resources,    'resources',    []),
]

urlpatterns = []

for canonical, view, name, aliases in WIDGETS:
    urlpatterns.append(path(canonical, view, name=name))
    # /words/ and friends land on /words rather than 404ing on the slash.
    for a in aliases + [canonical + '/']:
        urlpatterns.append(path(a, _alias('/' + canonical)))

urlpatterns += [
    # Kept so anything reversing widgets:home in a shared template still works.
    path('words', views.word_counter, name='home'),

    # The way through to the full tracker, which lives on its own hostname.
    path('app', _alias(settings.TRACKER_URL), name='full_app'),
    path('full-app', _alias(settings.TRACKER_URL)),

    # Path-preserving, so /app/colleges/ lands on the tracker's own /colleges/
    # rather than dumping you on its front page.
    re_path(r'^app/(?P<rest>.*)$', RedirectView.as_view(
        url=settings.TRACKER_URL.rstrip('/') + '/%(rest)s', query_string=True)),
    re_path(r'^full-app/(?P<rest>.*)$', RedirectView.as_view(
        url=settings.TRACKER_URL.rstrip('/') + '/%(rest)s', query_string=True)),

    # Autosave endpoint for the word counter and focus write. A real route,
    # not a redirect — a 302 would drop the POST body.
    path('scratchpad/<slug:slot>/save/', views.scratchpad_save, name='scratchpad_save'),
]
