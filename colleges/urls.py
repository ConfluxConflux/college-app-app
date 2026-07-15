from django.urls import path
from . import views

app_name = 'colleges'

urlpatterns = [
    path('', views.college_list, name='list'),
    path('all/', views.college_list, {'tab': 'all'}, name='list_all'),
    path('map/', views.college_map, name='map'),
    path('json/', views.college_json, name='json'),
    path('add-row/', views.college_add_row, name='add_row'),
    path('search-suggestions/', views.college_search_suggestions, name='search_suggestions'),
    path('quick-add/', views.college_quick_add, name='quick_add'),
    path('reorder/', views.college_reorder, name='reorder'),
    path('<int:pk>/remove/', views.college_remove, name='remove'),
    path('<int:pk>/update/', views.college_update, name='update'),
    path('<int:pk>/edit/<str:field>/', views.college_edit_cell, name='edit_cell'),
    # All Colleges addresses cells by canonical College pk; the UserCollege is
    # created on first edit.
    path('canonical/<int:college_pk>/edit/<str:field>/', views.college_canonical_cell, name='canonical_cell'),
]
