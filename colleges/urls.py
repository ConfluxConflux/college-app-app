from django.urls import path
from . import views

app_name = 'colleges'

urlpatterns = [
    path('', views.college_list, name='list'),
    path('all/', views.college_list, {'tab': 'all'}, name='list_all'),
    path('json/', views.college_json, name='json'),
    path('add/', views.college_add, name='add'),
    path('add-row/', views.college_add_row, name='add_row'),
    path('search-suggestions/', views.college_search_suggestions, name='search_suggestions'),
    path('quick-add/', views.college_quick_add, name='quick_add'),
    path('<int:pk>/', views.college_detail, name='detail'),
    path('<int:pk>/delete/', views.college_delete, name='delete'),
    path('<int:pk>/update/', views.college_update, name='update'),
    path('<int:pk>/edit/<str:field>/', views.college_edit_cell, name='edit_cell'),
]
