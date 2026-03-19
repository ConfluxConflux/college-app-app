from django.urls import path
from . import views

app_name = 'colleges'

urlpatterns = [
    path('', views.college_list, name='list'),
    path('json/', views.college_json, name='json'),
    path('add/', views.college_add, name='add'),
    path('<int:pk>/', views.college_detail, name='detail'),
    path('<int:pk>/delete/', views.college_delete, name='delete'),
    path('<int:pk>/update/', views.college_update, name='update'),
    path('<int:pk>/edit/<str:field>/', views.college_edit_cell, name='edit_cell'),
]
