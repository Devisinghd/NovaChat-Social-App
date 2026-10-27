import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Thread, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'chat_{self.thread_id}'
        self.user = self.scope['user']

        # 1. Guard: Reject unauthenticated users immediately
        if not self.user.is_authenticated:
            await self.close()
            return

        # 2. Guard: Verify the user is an allowed participant of the thread
        is_participant = await self.check_membership(self.user, self.thread_id)
        if not is_participant:
            print(f">>> Unauthorized access attempt blocked for user: {self.user.username}")
            await self.close() # Closes the connection immediately without calling accept()
            return

        # 3. Accept connection if both checks pass
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f">>> Websocket connection accepted for user: {self.user.username}")

    async def disconnect(self, close_code):
        # Only discard from channel layer if the connection was actually accepted
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data['message']

        # Double check authentication on incoming frames
        if self.user.is_authenticated:
            await self.save_message(self.user, self.thread_id, message_content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message_content,
                    'username': self.user.username,
                },
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
        }))

    @database_sync_to_async
    def check_membership(self, user, thread_id):
        """ Checks database to see if user belongs to the requested thread """
        try:
            thread = Thread.objects.get(id=thread_id)
            return thread.participants.filter(id=user.id).exists()
        except Thread.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user, thread_id, content):
        thread = Thread.objects.get(id=thread_id)
        thread.save() 
        return Message.objects.create(thread=thread, sender=user, chat_content=content)
