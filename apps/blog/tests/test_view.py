from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import os
from django.utils import timezone
from datetime import timedelta
from ..models import Post, Category, Comment
from ..forms import PostCreateForm, PostUpdateForm, CommentCreateForm, SearchForm

User = get_user_model()


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

        # Создаем общие посты, которые могут использоваться во всех тестах
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

    def setUp(self):
        super().setUp()
        self.client = Client()


class PostListViewTest(BlogViewsBaseTest):
    def setUp(self):
        super().setUp()

        # Создаем 5 черновиков для проверки того, что они не отображаются.
        self.draft_posts = []
        for i in range(5):
            post = Post.objects.create(
                title=f'Draft Post {i}',
                slug=f'draft-post-{i}',
                description=f'Description for draft post {i}',
                text=f'Full text for draft post {i}',
                author=self.user,
                category=self.category,
                status='draft',
            )
            self.draft_posts.append(post)

    def test_post_list_view_url_exists_at_desired_location(self):
        """Проверяет, что URL главной страницы доступен."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_post_list_view_uses_correct_template(self):
        """Проверяет, что PostListView использует правильный шаблон."""
        response = self.client.get(reverse('blog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_list.html')

    def test_post_list_view_shows_only_published_posts(self):
        """
        Проверяет, что PostListView отображает только посты со статусом 'published'.
        """
        response = self.client.get(reverse('blog:home'))

        # Проверяем, что в контексте содержатся только опубликованные посты
        self.assertNotIn(self.draft_post_1, response.context['posts'])
        self.assertIn(self.published_post_1, response.context['posts'])

        # Также проверяем, что ни один из 5 черновиков не попал на страницу
        for draft_post in self.draft_posts:
            self.assertNotIn(draft_post, response.context['posts'])

    def test_post_list_view_context_data(self):
        """
        Проверяет, что PostListView передает правильные данные в контекст.
        """
        response = self.client.get(reverse('blog:home'))
        self.assertEqual(response.status_code, 200)

        # Проверяем наличие и значение 'title'
        self.assertIn('title', response.context)
        self.assertEqual(response.context['title'], 'Главная страница')

