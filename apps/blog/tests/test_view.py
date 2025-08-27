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


class UserPostListViewTest(BlogViewsBaseTest):
    def setUp(self):
        super().setUp()
        self.user = self.user  # Используем пользователя из родительского класса
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )

        # Создаем посты для нашего пользователя
        self.my_published_post_1 = Post.objects.create(
            title='My Published Post 1',
            slug='my-published-post-1',
            text='text',
            author=self.user,
            status='published'
        )
        self.my_draft_post_1 = Post.objects.create(
            title='My Draft Post 1',
            slug='my-draft-post-1',
            text='text',
            author=self.user,
            status='draft'
        )

        # Создаем посты для другого пользователя
        self.other_user_published_post = Post.objects.create(
            title='Other Users Published Post',
            slug='other-users-published-post',
            text='text',
            author=self.other_user,
            status='published'
        )

    def test_view_redirects_for_unauthenticated_user(self):
        """
        Проверяет, что неавторизованного пользователя перенаправляет на страницу входа.
        """
        response = self.client.get(reverse('blog:my_posts'))
        self.assertEqual(response.status_code, 302)  # 302 Found
        self.assertRedirects(response, reverse('accounts:login') + '?next=' + reverse('blog:my_posts'))

    def test_view_url_exists_for_authenticated_user(self):
        """
        Проверяет, что URL доступен для авторизованного пользователя.
        """
        self.client.login(username='testuser_views', password='password123')
        response = self.client.get(reverse('blog:my_posts'))
        self.assertEqual(response.status_code, 200)

    def test_view_shows_only_current_users_published_posts(self):
        """
        Проверяет, что представление отображает только опубликованные посты
        текущего пользователя.
        """
        self.client.login(username='testuser_views', password='password123')
        response = self.client.get(reverse('blog:my_posts'))

        # Проверяем, что в списке есть наши опубликованные посты
        self.assertIn(self.my_published_post_1, response.context['posts'])

        # Проверяем, что в списке нет наших черновиков
        self.assertNotIn(self.my_draft_post_1, response.context['posts'])

        # Проверяем, что в списке нет постов другого пользователя
        self.assertNotIn(self.other_user_published_post, response.context['posts'])

    def test_view_uses_correct_template(self):
        """
        Проверяет, что представление использует правильный шаблон.
        """
        self.client.login(username='testuser_views', password='password123')
        response = self.client.get(reverse('blog:my_posts'))
        self.assertTemplateUsed(response, 'blog/user_posts.html')

    def test_view_context_data(self):
        """
        Проверяет, что в контекст передаются правильные данные.
        """
        self.client.login(username='testuser_views', password='password123')
        response = self.client.get(reverse('blog:my_posts'))
        self.assertEqual(response.context['title'], 'Мои статьи')


class PostDetailViewTest(BlogViewsBaseTest):
    def test_post_detail_view_url_exists(self):
        """Проверяет, что URL для опубликованного поста существует."""
        response = self.client.get(reverse('blog:post_detail', args=[self.published_post_1.slug]))
        self.assertEqual(response.status_code, 200)

    def test_post_detail_view_uses_correct_template(self):
        """Проверяет, что представление использует правильный шаблон."""
        response = self.client.get(reverse('blog:post_detail', args=[self.published_post_1.slug]))
        self.assertTemplateUsed(response, 'blog/post_detail.html')

    def test_post_detail_view_context_data(self):
        """Проверяет, что контекст содержит правильные данные."""
        response = self.client.get(reverse('blog:post_detail', args=[self.published_post_1.slug]))

        self.assertEqual(response.context['post'], self.published_post_1)
        self.assertEqual(response.context['title'], self.published_post_1.title)
        self.assertIsInstance(response.context['form'], CommentCreateForm)

    def test_post_detail_view_for_nonexistent_post(self):
        """
        Проверяет, что представление возвращает 404 для несуществующего поста.
        """
        response = self.client.get(reverse('blog:post_detail', args=['non-existent-slug']))
        self.assertEqual(response.status_code, 404)

    def test_post_detail_view_does_not_show_draft_post(self):
        """
        Проверяет, что представление возвращает 404 для поста со статусом 'draft'.
        """
        response = self.client.get(reverse('blog:post_detail', args=[self.draft_post_1.slug]))
        self.assertEqual(response.status_code, 404)


class PostFromCategoryTest(BlogViewsBaseTest):
    def setUp(self):
        super().setUp()

        # Создаем вторую категорию и посты для нее
        self.other_category = Category.objects.create(
            title='Other Category',
            slug='other-category'
        )
        self.post_in_other_category = Post.objects.create(
            title='Post in Other Category',
            slug='post-in-other-category',
            text='Text for other category post',
            author=self.user,
            category=self.other_category,
            status='published'
        )
        self.draft_in_other_category = Post.objects.create(
            title='Draft in Other Category',
            slug='draft-in-other-category',
            text='Draft text for other category post',
            author=self.user,
            category=self.other_category,
            status='draft'
        )

    def test_view_exists_for_valid_category(self):
        """
        Проверяет, что URL доступен для существующей категории.
        """
        response = self.client.get(reverse('blog:post_by_category', args=[self.category.slug]))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        """
        Проверяет, что представление использует правильный шаблон.
        """
        response = self.client.get(reverse('blog:post_by_category', args=[self.category.slug]))
        self.assertTemplateUsed(response, 'blog/post_list.html')

    def test_view_shows_only_posts_from_the_specified_category(self):
        """
        Проверяет, что представление показывает только опубликованные посты
        из нужной категории.
        """
        response = self.client.get(reverse('blog:post_by_category', args=[self.category.slug]))

        # Проверяем, что в списке есть посты из этой категории
        self.assertIn(self.published_post_1, response.context['posts'])

        # Проверяем, что в списке нет постов из другой категории
        self.assertNotIn(self.post_in_other_category, response.context['posts'])

    def test_view_does_not_show_drafts(self):
        """
        Проверяет, что представление не показывает черновики,
        даже если они принадлежат нужной категории.
        """
        response = self.client.get(reverse('blog:post_by_category', args=[self.category.slug]))

        # Проверяем, что черновик из нужной категории не отображается
        self.assertNotIn(self.draft_post_1, response.context['posts'])

    def test_view_returns_404_for_nonexistent_category(self):
        """
        Проверяет, что представление возвращает 404 для несуществующей категории.
        """
        response = self.client.get(reverse('blog:post_by_category', args=['non-existent-category']))
        self.assertEqual(response.status_code, 404)

    def test_view_context_data(self):
        """
        Проверяет, что в контекст передается правильный заголовок.
        """
        response = self.client.get(reverse('blog:post_by_category', args=[self.category.slug]))
        self.assertEqual(response.context['title'], f"Категория: {self.category.title}")


class PostCreateViewTest(BlogViewsBaseTest):
    def setUp(self):
        super().setUp()
        self.client.login(username='testuser_views', password='password123')
        self.url = reverse('blog:post_create')

    def test_view_redirects_for_unauthenticated_user(self):
        """Проверяет, что неавторизованного пользователя перенаправляет."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        # Исправляем проверку редиректа, чтобы она учитывала параметр 'next'
        expected_url = f"{reverse('blog:home')}?next={self.url}"
        self.assertRedirects(response, expected_url, status_code=302, target_status_code=200)

    def test_view_uses_correct_template_and_context(self):
        """Проверяет, что используется правильный шаблон и контекст."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_create.html')
        self.assertEqual(response.context['title'], 'Добавление статьи на сайт')
        self.assertIsInstance(response.context['form'], PostCreateForm)

    def test_post_creation_with_valid_data(self):
        """Проверяет, что новый пост создается с валидными данными."""
        initial_post_count = Post.objects.count()

        form_data = {
            'title': 'New Test Post',
            'slug': 'new-test-post',
            'description': 'A new test post description.',
            'text': 'The full text of the new test post.',
            'category': self.category.pk,
            'status': 'published',
        }
        response = self.client.post(self.url, data=form_data)

        # Проверяем, что количество постов увеличилось
        self.assertEqual(Post.objects.count(), initial_post_count + 1)

        # Проверяем, что новый пост был создан
        new_post = Post.objects.get(title='New Test Post')
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.status, 'published')

        # Проверяем, что после создания происходит редирект
        expected_redirect_url = reverse('blog:post_detail', kwargs={'slug': new_post.slug})
        self.assertRedirects(response, expected_redirect_url, status_code=302, target_status_code=200)

    def test_post_creation_with_invalid_data(self):
        """Проверяет, что пост не создается с невалидными данными."""
        initial_post_count = Post.objects.count()

        form_data = {
            'title': '',  # Невалидные данные (пустое поле)
            'description': 'An invalid post description.',
            'text': 'Invalid text.',
            'category': self.category.pk,
            'status': 'published',
        }
        response = self.client.post(self.url, data=form_data)

        # Проверяем, что пост не был создан
        self.assertEqual(Post.objects.count(), initial_post_count)

        # Проверяем, что статус-код 200 (форма снова отображается)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_create.html')

        self.assertTrue(response.context['form'].errors)
        self.assertIn('title', response.context['form'].errors)


class PostUpdateViewTest(BlogViewsBaseTest):
    def setUp(self):
        super().setUp()
        self.post = self.published_post_1
        self.url = reverse('blog:post_update', kwargs={'slug': self.post.slug})

    def test_view_redirects_for_unauthenticated_user(self):
        """
        Проверяет, что неавторизованного пользователя перенаправляет на страницу входа.
        """
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        expected_url = f"{reverse('blog:home')}?next={self.url}"
        self.assertRedirects(response, expected_url)

    def test_view_allows_author(self):
        """
        Проверяет, что автор поста может получить доступ к странице обновления.
        """
        self.client.login(username=self.user.username, password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template_and_context(self):
        """
        Проверяет, что используется правильный шаблон и контекст.
        """
        self.client.login(username=self.user.username, password='password123')
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'blog/post_update.html')
        self.assertEqual(response.context['title'], f'Обновление статьи: {self.post.title}')
        self.assertIsInstance(response.context['form'], PostUpdateForm)

    def test_post_update_with_valid_data(self):
        """
        Проверяет, что пост успешно обновляется с валидными данными.
        """
        self.client.login(username=self.user.username, password='password123')
        updated_title = 'Updated Title'
        form_data = {
            'title': updated_title,
            'description': self.post.description,
            'text': self.post.text,
            'category': self.post.category.pk,
            'status': self.post.status,
        }
        response = self.client.post(self.url, data=form_data)

        # Перезагружаем пост из базы, чтобы проверить изменения
        self.post.refresh_from_db()

        # Проверяем, что поле 'title' было обновлено
        self.assertEqual(self.post.title, updated_title)

        # Проверяем, что поле 'updater' было установлено
        self.assertEqual(self.post.updater, self.user)

        # Проверяем редирект на страницу детали поста
        expected_redirect_url = reverse('blog:post_detail', kwargs={'slug': self.post.slug})
        self.assertRedirects(response, expected_redirect_url, status_code=302, target_status_code=200)

    def test_post_update_with_invalid_data(self):
        """
        Проверяет, что пост не обновляется с невалидными данными.
        """
        self.client.login(username=self.user.username, password='password123')
        initial_title = self.post.title
        form_data = {
            'title': '',  # Невалидные данные
            'description': self.post.description,
            'text': self.post.text,
            'category': self.post.category.pk,
            'status': self.post.status,
        }
        response = self.client.post(self.url, data=form_data)

        # Проверяем, что статус-код 200 (форма снова отображается)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/post_update.html')

        # Проверяем, что пост не был обновлен
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, initial_title)

    def test_post_update_with_draft(self):
        """
        Проверяет, что черновик тоже можно обновить.
        """
        self.client.login(username=self.user.username, password='password123')
        draft_url = reverse('blog:post_update', kwargs={'slug': self.draft_post_1.slug})
        updated_title = 'Updated Draft Title'
        form_data = {
            'title': updated_title,
            'description': self.draft_post_1.description,
            'text': self.draft_post_1.text,
            'category': self.draft_post_1.category.pk,
            'status': 'published',  # Меняем статус на 'published'
        }
        response = self.client.post(draft_url, data=form_data)

        self.draft_post_1.refresh_from_db()
        self.assertEqual(self.draft_post_1.title, updated_title)
        self.assertEqual(self.draft_post_1.status, 'published')
        self.assertRedirects(response, reverse('blog:post_detail', kwargs={'slug': self.draft_post_1.slug}))


class CommentCreateViewTest(BlogViewsBaseTest):
    def setUp(self):
        super().setUp()

        self.user = self.__class__.user
        self.post = self.__class__.published_post_1

        # Исправлено: теперь используется 'content' вместо 'text'
        self.parent_comment = Comment.objects.create(
            content='Parent comment text.',
            post=self.post,
            author=self.user
        )

        self.url = reverse('blog:comment_create_view', kwargs={'pk': self.post.pk})

    def test_unauthenticated_user_receives_403_for_ajax_request(self):
        """Проверяет, что неавторизованный пользователь получает 403 при AJAX-запросе."""
        self.client.logout()
        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'application/json')
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Необходимо авторизоваться для добавления комментариев.')

    def test_comment_creation_with_valid_data_and_redirects(self):
        """Проверяет успешное создание комментария и перенаправление."""
        self.client.login(username=self.user.username, password='password123')
        initial_comment_count = Comment.objects.count()
        form_data = {'content': 'This is a new comment.'}

        response = self.client.post(self.url, data=form_data, HTTP_ACCEPT='text/html')

        self.assertEqual(Comment.objects.count(), initial_comment_count + 1)
        new_comment = Comment.objects.last()
        self.assertEqual(new_comment.author, self.user)
        self.assertEqual(new_comment.post, self.post)
        self.assertRedirects(response, reverse('blog:post_detail', kwargs={'slug': self.post.slug}))

    def test_comment_creation_with_invalid_data_and_no_redirects(self):
        """Проверяет, что невалидный запрос не создает комментарий."""
        self.client.login(username=self.user.username, password='password123')
        initial_comment_count = Comment.objects.count()
        form_data = {'content': ''}  # Невалидные данные

        response = self.client.post(self.url, data=form_data, HTTP_ACCEPT='text/html')

        self.assertEqual(Comment.objects.count(), initial_comment_count)
        self.assertEqual(response.status_code, 200)

    def test_ajax_comment_creation_with_valid_data(self):
        """Проверяет успешное создание комментария с помощью AJAX."""
        self.client.login(username=self.user.username, password='password123')
        initial_comment_count = Comment.objects.count()
        form_data = {'content': 'This is an AJAX comment.'}
        response = self.client.post(self.url, data=form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(Comment.objects.count(), initial_comment_count + 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('comment_html', response_data)

    def test_ajax_comment_creation_with_invalid_data(self):
        """Проверяет, что невалидный AJAX-запрос возвращает 400."""
        self.client.login(username=self.user.username, password='password123')
        initial_comment_count = Comment.objects.count()
        form_data = {'content': ''}  # Невалидные данные
        response = self.client.post(self.url, data=form_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(Comment.objects.count(), initial_comment_count)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-Type'], 'application/json')
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('errors', response_data)
