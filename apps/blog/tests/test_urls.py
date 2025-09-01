from django.test import TestCase, Client
from django.urls import reverse, resolve

from apps.blog.views import (
    PostListView, UserPostListView, PostDetailView, PostFromCategory,
    PostCreateView, PostUpdateView, CommentCreateView, RatingCreateView,
    PostSearchView
)
from apps.blog.tests.base import BlogViewsBaseTest


class BlogURLsTest(BlogViewsBaseTest):
    """
    Набор тестов для проверки маршрутизации URL-адресов блога.
    """

    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_home_url_resolves_to_post_list_view(self):
        """Проверяет, что URL '/' разрешается в PostListView."""
        url = reverse('blog:home')
        self.assertEqual(resolve(url).func.view_class, PostListView)

    def test_post_create_url_resolves_to_post_create_view(self):
        """Проверяет, что URL 'post/create/' разрешается в PostCreateView."""
        url = reverse('blog:post_create')
        self.assertEqual(resolve(url).func.view_class, PostCreateView)

    def test_post_update_url_resolves_to_post_update_view(self):
        """Проверяет, что URL 'post/<slug>/update/' разрешается в PostUpdateView."""
        url = reverse('blog:post_update', kwargs={'slug': 'test-slug'})
        self.assertEqual(resolve(url).func.view_class, PostUpdateView)

    def test_post_detail_url_resolves_to_post_detail_view(self):
        """Проверяет, что URL 'post/<slug>' разрешается в PostDetailView."""
        url = reverse('blog:post_detail', kwargs={'slug': 'test-slug'})
        self.assertEqual(resolve(url).func.view_class, PostDetailView)

    def test_comment_create_view_url_resolves_correctly(self):
        """Проверяет, что URL для создания комментария разрешается в CommentCreateView."""
        url = reverse('blog:comment_create_view', kwargs={'pk': 1})
        self.assertEqual(resolve(url).func.view_class, CommentCreateView)
        self.assertEqual(resolve(url).kwargs['pk'], 1)

    def test_post_by_category_url_resolves_correctly(self):
        """Проверяет, что URL для категории разрешается в PostFromCategory."""
        url = reverse('blog:post_by_category', kwargs={'slug': 'test-category'})
        self.assertEqual(resolve(url).func.view_class, PostFromCategory)
        self.assertEqual(resolve(url).kwargs['slug'], 'test-category')

    def test_rating_url_resolves_to_rating_create_view(self):
        """Проверяет, что URL 'rating/' разрешается в RatingCreateView."""
        url = reverse('blog:rating')
        self.assertEqual(resolve(url).func.view_class, RatingCreateView)

    def test_post_search_url_resolves_to_post_search_view(self):
        """Проверяет, что URL 'search/' разрешается в PostSearchView."""
        url = reverse('blog:post_search')
        self.assertEqual(resolve(url).func.view_class, PostSearchView)

    def test_my_posts_url_resolves_to_user_post_list_view(self):
        """Проверяет, что URL 'my-posts/' разрешается в UserPostListView."""
        url = reverse('blog:my_posts')
        self.assertEqual(resolve(url).func.view_class, UserPostListView)
