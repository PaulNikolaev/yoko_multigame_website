from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import os

from ..models import Post, Category, Comment
from ..forms import PostCreateForm, PostUpdateForm, CommentCreateForm, SearchForm

User = get_user_model()


class BlogViewsBaseTest(TestCase):
    """
    Базовый класс для настройки общих данных и клиента для всех тестов представлений.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser_views', password='password123')
        cls.category = Category.objects.create(title='Test Category Views', slug='test-category-views')

        # Создаем опубликованный пост
        cls.post_published = Post.objects.create(
            title='Test Published Post',
            slug='test-published-post',
            description='Description for published post',
            text='Full text for published post.',
            category=cls.category,
            author=cls.user,
            status='published',
            fixed=False
        )
        # Создаем черновик поста (не должен отображаться на главной странице)
        cls.post_draft = Post.objects.create(
            title='Test Draft Post',
            slug='test-draft-post',
            description='Description for draft post',
            text='Full text for draft post.',
            category=cls.category,
            author=cls.user,
            status='draft',
            fixed=False
        )

        for i in range(1, 7):
            Post.objects.create(
                title=f'Pagination Post {i}',
                slug=f'pagination-post-{i}',
                description=f'Description for pagination post {i}',
                text=f'Full text for pagination post {i}.',
                category=cls.category,
                author=cls.user,
                status='published',
                fixed=False
            )

    def setUp(self):
        self.client = Client()


class PostListViewTest(BlogViewsBaseTest):
    """
    Тесты для представления PostListView.
    """

    def test_post_list_view_status_code(self):
        """
        Тест: Проверяем, что страница списка постов загружается успешно (статус 200 OK).
        """
        response = self.client.get(reverse('blog:home'))
        self.assertEqual(response.status_code, 200)
