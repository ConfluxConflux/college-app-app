from django.conf import settings
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('homepage-1', views.landing, {'pin_version': 1}, name='landing_v1'),
    path('homepage-2', views.landing, {'pin_version': 2}, name='landing_v2'),
    path('dashboard/', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('core-activities/add/', views.core_activity_add, name='core_activity_add'),
    path('core-activities/<int:pk>/cell/<str:field>/', views.core_activity_cell, name='core_activity_cell'),
    path('core-activities/<int:pk>/delete/', views.core_activity_delete, name='core_activity_delete'),
    path('core-activities/<int:pk>/uc-cell/<str:field>/', views.core_activity_uc_cell, name='core_activity_uc_cell'),
    path('core-activities/<int:pk>/ca-cell/<str:field>/', views.core_activity_ca_cell, name='core_activity_ca_cell'),
    path('core-activities/<int:pk>/honor-cell/<str:field>/', views.core_activity_honor_cell, name='core_activity_honor_cell'),
    path('core-activities/<int:pk>/mit-cell/<str:field>/', views.core_activity_mit_cell, name='core_activity_mit_cell'),
    path('are-you-sure', views.are_you_sure, name='are_you_sure'),
    path('feedback/', views.feedback, name='feedback'),
]

# switch_applicant logs you in as an arbitrary applicant with no credentials.
# The route must not exist off localhost.
if settings.DEBUG:
    urlpatterns += [
        path('switch-applicant/<int:pk>/', views.switch_applicant, name='switch_applicant'),
    ]
