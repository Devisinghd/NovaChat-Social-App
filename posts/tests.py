from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User

from users.models import Profile
from users.models import Follow

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

    def test_feed_only_shows_follow_action_for_other_authors(self):
        other_user = User.objects.create_user(
            username='other-author',
            password='test-password',
        )
        Profile.objects.create(user=other_user)
        Post.objects.create(user=other_user, title='Another author post')
        self.client.force_login(self.user)

        response = self.client.get('/posts/feed/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['post_user'], self.user.username)
        self.assertContains(response, 'Follow other-author')
        self.assertNotContains(response, 'Follow feed-user')

    def test_follow_action_in_feed_toggles_and_returns_to_feed(self):
        other_user = User.objects.create_user(
            username='other-author',
            password='test-password',
        )
        Profile.objects.create(user=other_user)
        Post.objects.create(user=other_user, title='Another author post')
        self.client.force_login(self.user)

        response = self.client.post(
            '/toggle_follow/other-author/',
            {'next': '/posts/feed/'},
        )

        self.assertRedirects(response, '/posts/feed/')
        self.assertTrue(Follow.objects.filter(follower=self.user, following=other_user).exists())
        self.assertContains(self.client.get('/posts/feed/'), 'Following')


class PostCommentsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='thread-author',
            password='test-password',
        )
        Profile.objects.create(user=self.user)
        self.commenter = User.objects.create_user(
            username='commenter',
            password='test-password',
        )
        Profile.objects.create(user=self.commenter)
        self.post = Post.objects.create(
            user=self.user,
            title='A thread post',
            caption='Join the conversation',
        )
        self.url = f'/posts/{self.post.pk}/comments/'

    def test_comments_page_shows_post_and_all_comments(self):
        Comments.objects.create(
            post=self.post,
            author=self.commenter,
            posted_by=self.commenter.username,
            body='First reply',
        )
        Comments.objects.create(
            post=self.post,
            author=self.user,
            posted_by='thread-author',
            body='Second reply',
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A thread post')
        self.assertContains(response, 'Join the conversation')
        self.assertContains(response, 'First reply')
        self.assertContains(response, 'Second reply')
        self.assertContains(
            response,
            '<strong><a href="/profile/commenter/">commenter</a></strong>',
            html=True,
        )
        self.assertEqual(response.context['comments'].count(), 2)

    def test_authenticated_user_can_add_a_comment(self):
        self.client.login(username='thread-author', password='test-password')

        response = self.client.post(self.url, {'body': 'A new reply'})

        self.assertRedirects(response, self.url)
        comment = Comments.objects.get(post=self.post)
        self.assertEqual(comment.body, 'A new reply')
        self.assertEqual(comment.posted_by, 'thread-author')
        self.assertEqual(comment.author, self.user)

    def test_comment_authors_with_profile_photos_render_their_avatars(self):
        self.client.force_login(self.user)
        photo = SimpleUploadedFile(
            'avatar.png',
            b'not-a-real-image',
            content_type='image/png',
        )
        self.commenter.profile.photo = photo
        self.commenter.profile.save()
        Comments.objects.create(
            post=self.post,
            author=self.commenter,
            posted_by=self.commenter.username,
            body='A reply with a profile',
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.commenter.profile.photo.url)
        self.assertContains(response, f'/profile/{self.commenter.username}/')
        self.assertContains(
            response,
            f'<strong><a href="/profile/{self.commenter.username}/">commenter</a></strong>',
            html=True,
        )

    def test_missing_post_returns_not_found(self):
        response = self.client.get('/posts/99999/comments/')

        self.assertEqual(response.status_code, 404)
