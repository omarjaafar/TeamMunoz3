from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='accounts.signup'),
    path('login/', views.login, name='accounts.login'),
    path('logout/', views.logout, name='accounts.logout'),
    path('privacy/', views.edit_privacy, name='accounts.edit_privacy'),
    path('edit-profile/', views.edit_profile, name='accounts.edit_profile'),
    
    path("recruiter/candidates/search/", views.candidate_search, name="accounts.candidate_search"),
    path("recruiter/candidates/saved/", views.candidate_saved_search_list, name="accounts.candidate_saved_search_list"),
    path("recruiter/candidates/saved/new/", views.candidate_saved_search_create, name="accounts.candidate_saved_search_create"),
    path("recruiter/candidates/saved/<int:pk>/delete/", views.candidate_saved_search_delete, name="accounts.candidate_saved_search_delete"),
    path("recruiter/candidates/saved/<int:pk>/toggle-email/", views.candidate_saved_search_toggle_email, name="accounts.candidate_saved_search_toggle_email"),
    path("recruiter/candidates/saved/<int:pk>/notifications/", views.candidate_saved_search_notifications, name="accounts.candidate_saved_search_notifications"),
]
