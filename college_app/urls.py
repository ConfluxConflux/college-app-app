from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('', include('core.urls')),
    path('colleges/', include('colleges.urls')),
    path('activities/', include('activities.urls')),
    path('essays/', include('supplements.urls')),
    path('widgets/', include('widgets.urls')),
    path('admin/', admin.site.urls),
]
