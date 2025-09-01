from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.blog.models import Post, Category, User

class BlogViewsBaseTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username='testuser_views',
            email='test_views@example.com',
            password='password123'
        )
        cls.category = Category.objects.create(
            title='Test Category Views',
            slug='test-category-views'
        )

        cls.published_post_1 = Post.objects.create(
            title='Test Published Post 1',
            slug='test-published-post-1',
            description='Short description for published post 1',
            text='Full text for published post 1',
            author=cls.user,
            category=cls.category,
            status='published',
        )

        cls.draft_post_1 = Post.objects.create(
            title='Test Draft Post 1',
            slug='test-draft-post-1',
            description='Short description for draft post 1',
            text='Full text for draft post 1',
            author=cls.user,
            category=cls.category,
            status='draft',
        )