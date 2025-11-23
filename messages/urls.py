from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='messages.index'),
    path('send_email/', views.send_email, name='messages.send_email'),
    path('email_inbox/', views.email_inbox, name='messages.email_inbox'),
    path('email/<int:email_id>/', views.email_thread, name='messages.email_thread'),
    path('email/inbound/', views.receive_inbound_email, name='messages.email_inbound'),
    path('thread/<int:user_id>/', views.thread_view, name='messages.thread'),
    path('send/', views.send_message, name='messages.send_message'),
]