from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    path('', views.redirect_to_uc, name='home'),
    path('uc/', views.activities_home, {'tab': 'uc'}, name='home_uc'),
    path('common/', views.activities_home, {'tab': 'common_app'}, name='home_common'),
    path('mit/', views.activities_home, {'tab': 'mit'}, name='home_mit'),
    path('compare/', views.activities_home, {'tab': 'compare'}, name='home_compare'),
    path('brainstorm/', views.activities_home, {'tab': 'centralized'}, name='home_brainstorm'),
    path('estimator/', views.estimator_standalone, name='home_estimator'),
    # UC
    path('uc/<int:pk>/set-time/', views.uc_set_time, name='uc_set_time'),
    path('uc/reorder/', views.uc_reorder, name='uc_reorder'),
    path('uc/slot/<int:slot>/add/', views.uc_slot_add, name='uc_slot_add'),
    path('uc/add/', views.uc_add, name='uc_add'),
    path('uc/<int:pk>/', views.uc_edit, name='uc_edit'),
    path('uc/<int:pk>/cell/<str:field>/', views.uc_cell, name='uc_cell'),
    path('uc/<int:pk>/delete/', views.uc_delete, name='uc_delete'),
    # Common App Activities
    path('ca/reorder/', views.ca_reorder, name='ca_reorder'),
    path('ca/slot/<int:slot>/add/', views.ca_slot_add, name='ca_slot_add'),
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
    path('export/uc/csv/', views.export_uc_csv, name='export_uc_csv'),
    path('export/common-app/', views.export_common_app, name='export_common_app'),
    path('export/ca/', views.export_ca_txt, name='export_ca_txt'),
    path('export/ca/csv/', views.export_ca_csv, name='export_ca_csv'),
    path('export/honors/', views.export_honors_txt, name='export_honors_txt'),
    path('export/honors/csv/', views.export_honors_csv, name='export_honors_csv'),
    path('export/mit/', views.export_mit, name='export_mit'),
    # MIT
    path('mit/add/', views.mit_add, name='mit_add'),
    path('mit/<int:pk>/', views.mit_edit, name='mit_edit'),
    path('mit/<int:pk>/cell/<str:field>/', views.mit_cell, name='mit_cell'),
    path('mit/<int:pk>/delete/', views.mit_delete, name='mit_delete'),
]
