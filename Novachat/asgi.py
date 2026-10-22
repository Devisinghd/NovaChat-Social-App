import os
from django.core.asgi import get_asgi_application

# 1. Set the correct settings module for your project
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Novachat.settings')

# 2. Initialize the Django ASGI application early
django_asgi_app = get_asgi_application()

# 3. Import channels and routing AFTER get_asgi_application()
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import chat.routing

application = ProtocolTypeRouter({
    # Handles standard HTTP requests
    'http': django_asgi_app,
    
    # Handles WebSocket connections
    'websocket': AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
