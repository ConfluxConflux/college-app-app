from django.urls import path
from . import views

app_name = 'widgets'

urlpatterns = [
    path('', views.word_counter, name='home'),
    path('time-calculator/', views.estimator, name='estimator'),
    path('focus-write/', views.focus_write, name='focus_write'),
    path('scratchpad/<slug:slot>/save/', views.scratchpad_save, name='scratchpad_save'),
    path('pomodoros/', views.timer, name='timer'),
    path('word-counter/', views.word_counter, name='word_counter'),
    path('advice/', views.advice, name='advice'),
    path('resources/', views.resources, name='resources'),
]
