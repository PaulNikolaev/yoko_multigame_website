from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Sum
from unicodedata import category

from apps.blog.models import Post, Category, Rating
from apps.services.utils import unique_slugify
import os

User = get_user_model()


class PostModelTest(TestCase):
    """
    Набор тестов для модели Post.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Метод для настройки данных, которые будут использоваться во всех тестах.
        Выполняется один раз для всего класса тестов.
        """
        # Создаем тестового пользователя
        cls.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        # Создаем тестовую категорию
        cls.category = Category.objects.create(
            title='Тестовая категория',
            slug='test-category'
        )
        # Создаем тестовый пост
        cls.post = Post.objects.create(
            title='Тестовый Заголовок Поста',
            description='Это краткое описание тестового поста.',
            text='Полный текст тестового поста для проверки функциональности.',
            author=cls.user,
            category=cls.category,
            status='published',
            fixed=False
        )

    def test_post_creation(self):
        """
        Проверяет корректность создания объекта Post и его атрибутов.
        """
        post = self.post
        self.assertTrue(isinstance(post, Post))
        self.assertEqual(post.title, 'Тестовый Заголовок Поста')
        self.assertEqual(post.description, 'Это краткое описание тестового поста.')
        self.assertEqual(post.text, 'Полный текст тестового поста для проверки функциональности.')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.category, self.category)
        self.assertEqual(post.status, 'published')
        self.assertIsNotNone(post.create)
        self.assertIsNotNone(post.update)
        self.assertFalse(post.fixed)
        self.assertEqual(str(post), post.title)

    def test_slug_generation_on_save(self):
        """
        Проверяет, что слаг генерируется автоматически при сохранении и является уникальным,
        используя pytils и UUID для уникальности.
        """
        # 1. Проверяем слаг первого поста
        self.assertEqual(self.post.slug, 'testovyij-zagolovok-posta')

        # 2. Создаем второй пост с тем же заголовком, чтобы проверить уникальность слага
        new_post_with_same_title = Post.objects.create(
            title='Тестовый Заголовок Поста', # Тот же заголовок
            description='Второе описание.',
            text='Второй текст.',
            author=self.user,
            category=self.category,
            status='draft'
        )
        self.assertNotEqual(new_post_with_same_title.slug, 'testovyij-zagolovok-posta')
        self.assertTrue(new_post_with_same_title.slug.startswith('testovyij-zagolovok-posta-'))

        parts = new_post_with_same_title.slug.split('-')
        self.assertEqual(len(parts[-1]), 8)
        self.assertTrue(all(c in '0123456789abcdef' for c in parts[-1]))


        # 3. Проверяем, что при изменении заголовка слаг обновляется
        post_for_slug_check = Post.objects.create(
            title='Пост для проверки слага 2',
            description='Описание.',
            text='Текст.',
            author=self.user,
            category=self.category,
            status='published'
        )
        self.assertEqual(post_for_slug_check.slug, 'post-dlya-proverki-slaga-2')

        post_for_slug_check.title = 'Обновленный Заголовок Теста с Й'
        post_for_slug_check.save()
        self.assertEqual(post_for_slug_check.slug, 'obnovlennyij-zagolovok-testa-s-j')

    def test_post_status_choices(self):
        """
        Проверяет, что поле 'status' принимает только допустимые значения.
        """
        published_post = Post.objects.create(
            title='Опубликованный пост', description='desc', text='text', author=self.user, status='published'
        )
        self.assertEqual(published_post.status, 'published')

        draft_post = Post.objects.create(
            title='Черновик поста', description='desc', text='text', author=self.user, status='draft'
        )
        self.assertEqual(draft_post.status, 'draft')

        with self.assertRaises(ValidationError):
            invalid_status_post = Post(
                title='Неверный статус', description='desc', text='text', author=self.user, status='invalid_status'
            )
            invalid_status_post.full_clean()

    def test_get_sum_rating_method(self):
        """
        Проверяет корректность метода get_sum_rating.
        """
        self.assertEqual(self.post.get_sum_rating(), 0)

        Rating.objects.create(post=self.post, user=self.user, value=1)
        self.post.refresh_from_db()
        self.assertEqual(self.post.get_sum_rating(), 1)

        another_user = User.objects.create_user(username='anotheruser_for_rating_test', password='password')
        Rating.objects.create(post=self.post, user=another_user, value=-1)
        self.post.refresh_from_db()
        self.assertEqual(self.post.get_sum_rating(), 0)

        first_user_rating = Rating.objects.get(post=self.post, user=self.user)
        first_user_rating.value = -1
        first_user_rating.save()
        self.post.refresh_from_db()
        self.assertEqual(self.post.get_sum_rating(), -2)

        Rating.objects.filter(post=self.post).delete()
        self.post.refresh_from_db()
        self.assertEqual(self.post.get_sum_rating(), 0)

    def test_thumbnail_upload(self):
        """
        Проверяет, что изображение загружается и сохраняется правильно.
        """
        image_content = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xF9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b'
        uploaded_image_name = 'test_image.gif'
        uploaded_image = SimpleUploadedFile(
            name='test_image.gif',
            content=image_content,
            content_type='image/gif'
        )
        self.post.thumbnail = uploaded_image
        self.post.save()

        self.assertTrue(self.post.thumbnail.name.startswith('images/thumbnails/'))

        generated_filename = os.path.basename(self.post.thumbnail.name)
        self.assertTrue(uploaded_image_name.split('.')[0] in generated_filename)
        self.assertTrue(generated_filename.endswith('.gif'))

        # Проверяем валидатор расширения файла
        with self.assertRaises(ValidationError):
            invalid_file = SimpleUploadedFile(
                name='test.txt',
                content=b'some text',
                content_type='text/plain'
            )
            self.post.thumbnail = invalid_file
            self.post.full_clean()

    def test_category_on_delete_set_null(self):
        """
        Проверяет, что при удалении категории, поле category в Post устанавливается в NULL.
        """
        self.assertEqual(self.post.category, self.category)

        self.category.delete()

        self.post.refresh_from_db()
        self.assertIsNone(self.post.category)

    def test_author_on_delete_set_default(self):
        """
        Проверяет, что при удалении автора, поле author в Post устанавливается в default (1).
        """
        author_to_delete = User.objects.create_user(username='author_to_delete_test', password='pass')
        post_by_deleted_author = Post.objects.create(
            title='Пост для удаляемого автора',
            description='desc',
            text='text',
            author=author_to_delete,
            status='published'
        )
        self.assertEqual(post_by_deleted_author.author, author_to_delete)

        author_to_delete.delete()

        post_by_deleted_author.refresh_from_db()
        self.assertEqual(post_by_deleted_author.author, self.user)

    def test_updater_on_delete_set_null(self):
        """
        Проверяет, что при удалении updater, поле updater в Post устанавливается в NULL.
        """
        updater_user = User.objects.create_user(username='updateruser_test', password='password')
        self.post.updater = updater_user
        self.post.save()
        self.assertEqual(self.post.updater, updater_user)

        updater_user.delete()

        self.post.refresh_from_db()
        self.assertIsNone(self.post.updater)

    def test_post_manager_draft_status(self):
        """
        Проверяет, что custom manager PostManager.draft() возвращает только черновики.
        """
        draft_post_1 = Post.objects.create(
            title='Черновик 1', description='desc', text='text', author=self.user, status='draft'
        )
        Post.objects.create(
            title='Опубликованный 2', description='desc', text='text', author=self.user, status='published'
        )

        draft_posts = Post.custom.draft()
        self.assertEqual(draft_posts.count(), 1)  # Только draft_post_1
        self.assertEqual(draft_posts.first(), draft_post_1)

    def test_post_manager_published_status(self):
        """
        Проверяет, что custom manager PostManager.published() возвращает только опубликованные.
        """
        self.assertEqual(self.post.status, 'published')

        published_post_2 = Post.objects.create(
            title='Второй опубликованный пост',
            description='desc',
            text='text',
            author=self.user,
            status='published'
        )

        Post.objects.create(
            title='Черновик для теста',
            description='desc',
            text='text',
            author=self.user,
            status='draft'
        )

        published_posts = Post.custom.published()
        self.assertEqual(published_posts.count(), 2)
        self.assertIn(self.post, published_posts)
        self.assertIn(published_post_2, published_posts)

    def test_post_manager_fixed(self):
        """
        Проверяет, что custom manager PostManager.fixed_posts() возвращает только прикрепленные посты.
        """
        fixed_post_1 = Post.objects.create(
            title='Прикрепленный пост 1', description='desc', text='text', author=self.user, status='published',
            fixed=True
        )
        Post.objects.create(
            title='Обычный пост', description='desc', text='text', author=self.user, status='published', fixed=False
        )

        fixed_posts = Post.custom.fixed_posts()
        self.assertEqual(fixed_posts.count(), 1)
        self.assertEqual(fixed_posts.first(), fixed_post_1)


class CategoryModelTest(TestCase):
    """
    Набор тестов для модели Category.
    """
    @classmethod
    def setUpTestData(cls):
        """
        Метод для настройки данных, которые будут использоваться во всех тестах.
        """
        cls.category_data = {
            'title': 'Тестовая категория',
            'description': 'Это тестовое описание для категории.'
        }
        cls.category = Category.objects.create(**cls.category_data)

    def test_category_creating(self):
        """
        Проверяет корректность создания объекта Category и его атрибутов.
        """
        category = self.category
        self.assertTrue(isinstance(category, Category))
        self.assertEqual(category.title, self.category_data['title'])
        self.assertEqual(category.description, self.category_data['description'])
        self.assertIsNotNone(category.slug)
        self.assertNotEqual(category.slug, '')
        self.assertEqual(category.slug, 'testovaya-kategoriya')
        self.assertEqual(str(category), category.title)