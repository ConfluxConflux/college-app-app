"""Root URLconf for the widgets-only build (WIDGETS_ONLY=True).

Deliberately tiny: only the widget pages exist. No admin, no allauth, no
colleges/activities/essays/dashboard. Anything else 404s, so there is no way
to stumble into the half-finished parts of the tracker from here.
"""
from django.urls import include, path
from django.views.generic import RedirectView

from widgets import views as widget_views

urlpatterns = [
    path('', widget_views.welcome, name='welcome'),
    # Short links that predate /widgets/, kept working.
    path('time', RedirectView.as_view(url='/widgets/time-calculator/', permanent=True)),
    path('words', RedirectView.as_view(url='/widgets/word-counter/', permanent=True)),
    path('widgets/', include('widgets.urls')),
]
