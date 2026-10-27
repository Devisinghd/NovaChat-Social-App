from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Uses the secure internal database ID of the thread, keeping URLs unpredictable
    re_path(r'ws/chat/(?P<thread_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
]
