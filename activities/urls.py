from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    path('', views.activities_home, name='home'),
    # UC
    path('uc/reorder/', views.uc_reorder, name='uc_reorder'),
    path('uc/slot/<int:slot>/add/', views.uc_slot_add, name='uc_slot_add'),
    path('uc/add/', views.uc_add, name='uc_add'),
    path('uc/<int:pk>/', views.uc_edit, name='uc_edit'),
    path('uc/<int:pk>/cell/<str:field>/', views.uc_cell, name='uc_cell'),
    path('uc/<int:pk>/delete/', views.uc_delete, name='uc_delete'),
    # Common App Activities
    path('ca/add/', views.ca_add, name='ca_add'),
    path('ca/<int:pk>/', views.ca_edit, name='ca_edit'),
    path('ca/<int:pk>/cell/<str:field>/', views.ca_cell, name='ca_cell'),
    path('ca/<int:pk>/delete/', views.ca_delete, name='ca_delete'),
    # Common App Honors
    path('honors/add/', views.honor_add, name='honor_add'),
    path('honors/<int:pk>/', views.honor_edit, name='honor_edit'),
    path('honors/<int:pk>/cell/<str:field>/', views.honor_cell, name='honor_cell'),
    path('honors/<int:pk>/delete/', views.honor_delete, name='honor_delete'),
    # Exports
    path('export/uc/', views.export_uc, name='export_uc'),
    path('export/common-app/', views.export_common_app, name='export_common_app'),
    path('export/mit/', views.export_mit, name='export_mit'),
    # MIT
    path('mit/add/', views.mit_add, name='mit_add'),
    path('mit/<int:pk>/', views.mit_edit, name='mit_edit'),
    path('mit/<int:pk>/cell/<str:field>/', views.mit_cell, name='mit_cell'),
    path('mit/<int:pk>/delete/', views.mit_delete, name='mit_delete'),
]
