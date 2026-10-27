from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.chat_dashboard, name='chat_dashboard'),
    path('thread/<int:thread_id>/', views.chatroom, name='chatroom'),
    path('direct/<int:user_id>/', views.get_or_create_thread, name='open_dm'),
]
