from django.urls import path
from . import views

app_name = 'widgets'

urlpatterns = [
    path('', views.estimator, name='home'),
    path('estimator/', views.estimator, name='estimator'),
]
