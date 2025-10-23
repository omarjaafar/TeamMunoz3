from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='messages.index'),
    path('send/', views.send_message, name='messages.send_message'),
]