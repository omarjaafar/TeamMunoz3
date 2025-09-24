from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='home.index'),
    path('about', views.about, name='home.about'),
    # search (for both Job Seeker and Recruiter)
    path('jobs/search/', views.search, name='jobs.search'),
    # job seeker only
    path('seeker/apply/', views.seeker_apply, name='seeker.apply'),
    path('seeker/status/', views.seeker_status, name='seeker.status'),
    path('seeker/settings/', views.seeker_settings, name='seeker.settings'),
    path('seeker/profile/', views.seeker_profile, name='seeker.profile'),
    # recruiter only
    path('recruiter/post/', views.recruiter_post_job, name='recruiter.post_job'),
    path('recruiter/messages/', views.recruiter_messages, name='recruiter.messages'),
    # administrator only
    path('adminpanel/edit-posts/', views.admin_edit_posts, name='admin.edit_posts'),
]