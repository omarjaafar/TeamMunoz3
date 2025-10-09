from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='accounts.signup'),
    path('login/', views.login, name='accounts.login'),
    path('logout/', views.logout, name='accounts.logout'),
    path('privacy/', views.edit_privacy, name='accounts.edit_privacy'),
    path('edit-profile/', views.edit_profile, name='accounts.edit_profile'),
]
