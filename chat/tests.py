from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Message, Thread
from users.models import Follow


class ChatDashboardTests(TestCase):
    def test_dashboard_displays_followed_user_and_links_to_their_dm(self):
        current_user = User.objects.create_user(
            username='current-user',
            password='test-password',
        )
        chat_partner = User.objects.create_user(
            username='chat-partner',
            password='test-password',
        )
        follower = User.objects.create_user(
            username='incoming-follower',
            password='test-password',
        )
        Follow.objects.create(follower=current_user, following=chat_partner)
        Follow.objects.create(follower=follower, following=current_user)
        self.client.force_login(current_user)

        response = self.client.get(reverse('chat_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'chat-partner')
        self.assertContains(
            response,
            reverse('open_dm', args=[chat_partner.pk]),
        )
        self.assertNotContains(response, 'current-user')
        self.assertNotContains(response, 'incoming-follower')

    def test_inbox_shows_the_latest_message_preview(self):
        current_user = User.objects.create_user(
            username='inbox-owner',
            password='test-password',
        )
        chat_partner = User.objects.create_user(
            username='inbox-partner',
            password='test-password',
        )
        thread = Thread.objects.create()
        thread.participants.add(current_user, chat_partner)
        Message.objects.create(
            thread=thread,
            sender=chat_partner,
            chat_content='Earlier message',
        )
        Message.objects.create(
            thread=thread,
            sender=current_user,
            chat_content='Latest inbox preview',
        )
        self.client.force_login(current_user)

        response = self.client.get(reverse('chat_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'inbox-partner')
        self.assertContains(response, 'Latest inbox preview')
        self.assertContains(response, 'You')
        self.assertNotContains(response, 'Earlier message')


class ChatRoomTests(TestCase):
    def test_saved_message_content_is_rendered_as_text(self):
        sender = User.objects.create_user(
            username='message-sender',
            password='test-password',
        )
        recipient = User.objects.create_user(
            username='message-recipient',
            password='test-password',
        )
        thread = Thread.objects.create()
        thread.participants.add(sender, recipient)
        Message.objects.create(
            thread=thread,
            sender=sender,
            chat_content='<img src=x onerror=alert(1)>',
        )
        self.client.force_login(recipient)

        response = self.client.get(reverse('chatroom', args=[thread.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '&lt;img src=x onerror=alert(1)&gt;')
        self.assertNotContains(response, '<img src=x onerror=alert(1)>')

# Create your tests here.
