from django.test import TestCase
from django.contrib.auth.models import User

from .models import Profile
from posts.models import Post


class ProfileViewTests(TestCase):
	def test_profile_page_redirects_anonymous_users_to_login(self):
		response = self.client.get('/profile/')

		self.assertRedirects(response, '/login/?next=/profile/')

	def test_profile_page_renders_current_users_details(self):
		user = User.objects.create_user(username='profile-user', password='test-password')
		Profile.objects.create(user=user, bio='A profile bio')
		Post.objects.create(user=user, title='First post', caption='A post caption')
		self.client.force_login(user)

		response = self.client.get('/profile/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'profile-user')
		self.assertContains(response, 'A profile bio')
		self.assertContains(response, 'A post caption')
		self.assertContains(response, '0</strong> followers')

	def test_posts_page_uses_renamed_template_without_social_actions(self):
		user = User.objects.create_user(username='profile-user', password='test-password')
		Profile.objects.create(user=user)
		Post.objects.create(user=user, title='First post', caption='A post caption')
		self.client.force_login(user)

		response = self.client.get('/')

		self.assertTemplateUsed(response, 'users/posts.html')
		self.assertContains(response, 'A post caption')
		self.assertNotContains(response, 'btn-like')
		self.assertNotContains(response, 'Comment on')
		self.assertNotContains(response, 'Share First post')
