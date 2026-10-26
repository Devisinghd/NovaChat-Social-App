from django.urls import path

from . import views
from django.contrib.auth import views as auth_views
urlpatterns = [
    path('login/', views.user_login, name='login'),
    #path('logout/', views.user_logout, name='logout'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='users/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='users/password_change_done.html'), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html'), name='password_reset_complete'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='edit'),
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile, name='user_profile'),
    path('settings/', views.settings_page, name='settings_page'),
    path('toggle_follow/<str:username>/', views.toggle_follow, name='toggle_follow'),
    path('followers/<str:username>/', views.followers_list, name='followers_list'),
    path('following/<str:username>/', views.following_list, name='following_list'),
    path('followers/<str:username>/remove/', views.remove_follower, name='remove_follower'),
    path('search/', views.post_user_profile_search, name='post_user_profile_search'),
]
