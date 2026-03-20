from django.urls import path
from . import views

app_name = 'supplements'

urlpatterns = [
    path('', views.supplements_home, name='home'),
    path('<int:pk>/status/', views.essay_status_edit, name='essay_status'),
]
