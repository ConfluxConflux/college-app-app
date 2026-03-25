from django.urls import path
from colleges import views

app_name = 'applications'

urlpatterns = [
    path('', views.applications, name='home'),
    path('uc/', views.applications_uc, name='uc'),
    path('common/', views.applications_common, name='common'),
]
