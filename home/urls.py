from django.urls import path
from applications.views import MyApplicationsView
from . import views

urlpatterns = [
    path('', views.index, name='home.index'),
    path('about', views.about, name='home.about'),
   
    # job seeker only
    path('seeker/apply/', views.seeker_apply, name='seeker.apply'),
    path('seeker/status/', MyApplicationsView.as_view(), name='seeker.status'),
    path('seeker/settings/', views.seeker_settings, name='seeker.settings'),
    path('seeker/profile/', views.seeker_profile, name='seeker.profile'),

    # recruiter only
    path('recruiter/post/', views.recruiter_post_job, name='recruiter.post_job'),
    path('recruiter/messages/', views.recruiter_messages, name='recruiter.messages'),
    
    # administrator only
    path('adminpanel/edit-posts/', views.admin_edit_posts, name='admin.edit_posts'), #original
    path('adminpanel/edit-posts/<int:pk>/edit/', views.admin_edit_post, name='admin.edit_post'), #plus new
    path('adminpanel/edit-posts/<int:pk>/delete/', views.admin_delete_post, name='admin.delete_post'), #delete 
    path('adminpanel/manage-users/', views.admin_manage_users, name='admin.manage_users'),
    path('adminpanel/create-user/', views.admin_create_user, name='admin.create_user'),
    path('adminpanel/delete-user/<int:user_id>/', views.admin_delete_user, name='admin.delete_user'),
    path('admin/change-role/<int:user_id>/<str:new_role>/', views.change_role, name='admin.change_role'),
    path('adminpanel/change-role-post/<int:user_id>/', views.change_role_post, name='admin.change_role_post'),

]