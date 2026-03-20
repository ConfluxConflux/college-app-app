from django.urls import path
from . import views

app_name = 'supplements'

urlpatterns = [
    path('', views.supplements_home, name='home'),
    path('<int:pk>/status/', views.essay_status_edit, name='essay_status'),
    path('<int:pk>/save/', views.essay_save, name='essay_save'),
    path('<int:pk>/focus/', views.essay_focus, name='essay_focus'),
    path('<int:pk>/category/', views.essay_category_edit, name='essay_category'),
]
