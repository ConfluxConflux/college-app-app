from django.urls import path
from . import views

app_name = 'supplements'

urlpatterns = [
    path('', views.supplements_home, name='home'),
    path('<int:pk>/status/', views.essay_status_edit, name='essay_status'),
    path('<int:pk>/save/', views.essay_save, name='essay_save'),
    path('<int:pk>/focus/', views.essay_focus, name='essay_focus'),
    path('<int:pk>/category/', views.essay_category_edit, name='essay_category'),
    path('uc-piq/<int:pk>/status/', views.uc_piq_status_edit, name='uc_piq_status'),
    path('uc-piq/<int:pk>/save/', views.uc_piq_save, name='uc_piq_save'),
    path('common-essay/<int:pk>/status/', views.common_essay_status_edit, name='common_essay_status'),
    path('common-essay/<int:pk>/save/', views.common_essay_save, name='common_essay_save'),
]
