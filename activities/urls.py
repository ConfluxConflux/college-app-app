from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    path('', views.activities_home, name='home'),
    # UC
    path('uc/add/', views.uc_add, name='uc_add'),
    path('uc/<int:pk>/', views.uc_edit, name='uc_edit'),
    path('uc/<int:pk>/delete/', views.uc_delete, name='uc_delete'),
    # Common App Activities
    path('ca/add/', views.ca_add, name='ca_add'),
    path('ca/<int:pk>/', views.ca_edit, name='ca_edit'),
    path('ca/<int:pk>/delete/', views.ca_delete, name='ca_delete'),
    # Common App Honors
    path('honors/add/', views.honor_add, name='honor_add'),
    path('honors/<int:pk>/', views.honor_edit, name='honor_edit'),
    path('honors/<int:pk>/delete/', views.honor_delete, name='honor_delete'),
    # MIT
    path('mit/add/', views.mit_add, name='mit_add'),
    path('mit/<int:pk>/', views.mit_edit, name='mit_edit'),
    path('mit/<int:pk>/delete/', views.mit_delete, name='mit_delete'),
]
