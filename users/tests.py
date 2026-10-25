from django.test import TestCase
from django.contrib.auth.models import User

from .models import Follow, Profile
from posts.models import Post


class ProfileViewTests(TestCase):
	def test_login_redirects_to_home_feed(self):
		User.objects.create_user(username='login-user', password='test-password')

		response = self.client.post('/login/', {
			'username': 'login-user',
			'password': 'test-password',
		})

		self.assertRedirects(response, '/')

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
		self.assertContains(response, '<strong>0</strong><span>followers</span>', html=True)

	def test_profile_displays_actual_follower_and_following_accounts(self):
		profile_owner = User.objects.create_user(username='profile-owner', password='test-password')
		follower = User.objects.create_user(username='profile-follower', password='test-password')
		followed = User.objects.create_user(username='profile-followed', password='test-password')
		Profile.objects.create(user=profile_owner)
		Profile.objects.create(user=follower)
		Profile.objects.create(user=followed)
		Follow.objects.create(follower=follower, following=profile_owner)
		Follow.objects.create(follower=profile_owner, following=followed)
		self.client.force_login(profile_owner)

		response = self.client.get('/profile/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '<strong>1</strong><span>followers</span>', html=True)
		self.assertContains(response, '<strong>1</strong><span>following</span>', html=True)
		self.assertContains(response, '/followers/profile-owner/')
		self.assertContains(response, '/following/profile-owner/')

	def test_viewing_another_profile_offers_follow_and_unfollow(self):
		viewer = User.objects.create_user(username='profile-viewer', password='test-password')
		Profile.objects.create(user=viewer)
		profile_owner = User.objects.create_user(username='profile-owner', password='test-password')
		Profile.objects.create(user=profile_owner)
		self.client.force_login(viewer)

		response = self.client.get('/profile/profile-owner/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Follow')
		self.assertContains(response, '/toggle_follow/profile-owner/')

		response = self.client.post('/toggle_follow/profile-owner/')

		self.assertRedirects(response, '/profile/profile-owner/')
		self.assertTrue(Follow.objects.filter(follower=viewer, following=profile_owner).exists())
		response = self.client.get('/profile/profile-owner/')
		self.assertContains(response, 'Unfollow')

		response = self.client.post('/toggle_follow/profile-owner/')

		self.assertRedirects(response, '/profile/profile-owner/')
		self.assertFalse(Follow.objects.filter(follower=viewer, following=profile_owner).exists())

	def test_follow_action_requires_post_and_cannot_follow_self(self):
		self_user = User.objects.create_user(username='profile-user', password='test-password')
		Profile.objects.create(user=self_user)
		self.client.force_login(self_user)
		response = self.client.get('/toggle_follow/profile-user/')
		self.assertEqual(response.status_code, 405)

		response = self.client.post('/toggle_follow/profile-user/')

		self.assertRedirects(response, '/profile/profile-user/')
		self.assertFalse(Follow.objects.exists())

	def test_settings_page_uses_the_current_view_and_requires_login(self):
		response = self.client.get('/settings/')
		self.assertRedirects(response, '/login/?next=/settings/')

		user = User.objects.create_user(username='settings-user', password='test-password')
		Profile.objects.create(user=user)
		self.client.force_login(user)
		response = self.client.get('/settings/')

		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'users/settings.html')

	def test_follow_lists_render_accounts_and_actions(self):
		owner = User.objects.create_user(username='list-owner', password='test-password')
		follower = User.objects.create_user(username='list-follower', password='test-password')
		followed = User.objects.create_user(username='list-followed', password='test-password')
		for user in (owner, follower, followed):
			Profile.objects.create(user=user)
		Follow.objects.create(follower=follower, following=owner)
		Follow.objects.create(follower=owner, following=followed)
		self.client.force_login(owner)

		follower_response = self.client.get('/followers/list-owner/')
		following_response = self.client.get('/following/list-owner/')

		self.assertEqual(follower_response.status_code, 200)
		self.assertTemplateUsed(follower_response, 'users/follower_list.html')
		self.assertContains(follower_response, 'list-follower')
		self.assertContains(follower_response, 'Remove')
		self.assertEqual(following_response.status_code, 200)
		self.assertTemplateUsed(following_response, 'users/following_list.html')
		self.assertContains(following_response, 'list-followed')
		self.assertContains(following_response, 'Following')

	def test_owner_can_remove_a_follower_from_follower_list(self):
		owner = User.objects.create_user(username='list-owner', password='test-password')
		follower = User.objects.create_user(username='list-follower', password='test-password')
		Profile.objects.create(user=owner)
		Profile.objects.create(user=follower)
		Follow.objects.create(follower=follower, following=owner)
		self.client.force_login(owner)

		response = self.client.post('/followers/list-owner/remove/', {
			'follower': follower.username,
			'next': '/followers/list-owner/',
		})

		self.assertRedirects(response, '/followers/list-owner/')
		self.assertFalse(Follow.objects.filter(follower=follower, following=owner).exists())

	def test_homepage_renders_the_feed(self):
		user = User.objects.create_user(username='profile-user', password='test-password')
		Profile.objects.create(user=user)
		Post.objects.create(user=user, title='First post', caption='A post caption')
		self.client.force_login(user)

		response = self.client.get('/')

		self.assertTemplateUsed(response, 'posts/feed.html')
		self.assertContains(response, 'A post caption')
		self.assertContains(response, 'btn-like')
