from django.urls import path
from . import views

app_name = 'widgets'

urlpatterns = [
    path('', views.estimator, name='home'),
    path('estimator/', views.estimator, name='estimator'),
    path('focus-write/', views.focus_write, name='focus_write'),
    path('word-counter/', views.word_counter, name='word_counter'),
]
