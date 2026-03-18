from django.urls import path
from . import views

app_name = 'supplements'

urlpatterns = [
    path('', views.supplements_home, name='home'),
]
