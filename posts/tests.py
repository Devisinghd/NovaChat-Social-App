from django.test import TestCase
from django.contrib.auth.models import User

from users.models import Profile

from .models import Comments, Post


class FeedViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='feed-user',
            password='test-password',
        )
        Profile.objects.create(user=self.user)
        self.post = Post.objects.create(
            user=self.user,
            title='A feed post',
            caption='A short caption',
        )

    def test_feed_shows_only_two_latest_comments_and_links_to_full_thread(self):
        for index in range(5):
            Comments.objects.create(
                post=self.post,
                posted_by=self.user.username,
                body=f'Comment {index}',
            )

        response = self.client.get('/posts/feed/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comment 4')
        self.assertContains(response, 'Comment 3')
        self.assertNotContains(response, 'Comment 2')
        self.assertContains(response, 'View all 5 comments')
        self.assertContains(response, f'/posts/{self.post.id}/comments/')

    def test_feed_paginates_posts_ten_at_a_time(self):
        for index in range(10):
            Post.objects.create(user=self.user, title=f'Post {index}')

        first_page = self.client.get('/posts/feed/')
        second_page = self.client.get('/posts/feed/?page=2')

        self.assertEqual(first_page.status_code, 200)
        self.assertEqual(len(first_page.context['posts']), 10)
        self.assertContains(first_page, 'Older posts')
        self.assertEqual(second_page.status_code, 200)
        self.assertEqual(len(second_page.context['posts']), 1)
