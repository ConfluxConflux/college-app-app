from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('time', RedirectView.as_view(url='/widgets/time-calculator/', permanent=True)),
    # Redirects for old applications URLs
    path('colleges/applications/', RedirectView.as_view(url='/applications/', permanent=True, query_string=True)),
    path('colleges/applications/uc/', RedirectView.as_view(url='/applications/uc/', permanent=True)),
    path('colleges/applications/common/', RedirectView.as_view(url='/applications/common/', permanent=True)),
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')),
    path('colleges/', include('colleges.urls')),
    path('applications/', include('college_app.applications_urls')),
    path('activities/', include('activities.urls')),
    path('essays/', include('supplements.urls')),
    path('widgets/', include('widgets.urls')),
    path('admin/', admin.site.urls),
]
