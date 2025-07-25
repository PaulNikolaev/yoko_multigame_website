import os
import time
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.blog.models import Post, Category, Comment, Rating

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
            title='Тестовый Заголовок Поста',
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
        self.assertIsNone(post_by_deleted_author.author)
        self.assertTrue(Post.objects.filter(pk=post_by_deleted_author.pk).exists())

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

    def test_default_description(self):
        """
        Проверяет, что описание категории по умолчанию устанавливается в 'Нет описания'.
        """
        category_without_description = Category.objects.create(title='Категория Без Описания')
        self.assertEqual(category_without_description.description, 'Нет описания')

    def test_slug_generation(self):
        """
        Проверяет, что слаг генерируется автоматически при создании категории и является уникальным.
        """
        self.assertEqual(self.category.slug, 'testovaya-kategoriya')

        # Тест на уникальность слага
        category_with_same_title = Category.objects.create(
            title='Тестовая Категория',
            description='Другое описание'
        )
        self.assertNotEqual(category_with_same_title.slug, 'testovaya-kategoriya')
        self.assertTrue(category_with_same_title.slug, 'testovaya-kategoriya')

    def test_str_representation(self):
        """
        Проверяет корректность метода __str__.
        """
        self.assertEqual(str(self.category), self.category_data['title'])

    def test_blank_and_null_fields(self):
        """
        Проверяет, что поля description и slug корректно обрабатываются с blank/null.
        """
        category_blank_fields = Category.objects.create(title='Категория С Пустыми Полями')
        self.assertIsNotNone(category_blank_fields.slug)
        self.assertEqual(category_blank_fields.description, 'Нет описания')

        category_explicit_blank_desc = Category.objects.create(title='Explicit Blank', description='')
        self.assertEqual(category_explicit_blank_desc.description, '')


class CommentModelTest(TestCase):
    """
    Набор тестов для модели Comment.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Метод для настройки данных, которые будут использоваться во всех тестах.
        """
        cls.user = User.objects.create_user(username='test_comment_user', password='password')
        cls.category = Category.objects.create(title='Тестовая Категория Комментариев')
        cls.post = Post.objects.create(
            title='Тестовый Пост Для Комментариев',
            description='Описание.',
            text='Текст поста.',
            author=cls.user,  # <--- Убедитесь, что здесь автор указан
            category=cls.category,
            status='published'
        )

        # Создаем корневой комментарий
        cls.root_comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,  # <--- Убедитесь, что здесь автор указан
            content='Это корневой комментарий.',
            status='published'
        )
        time.sleep(0.05)
        # Создаем дочерний комментарий
        cls.child_comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,  # <--- Убедитесь, что здесь автор указан
            content='Это ответ на корневой комментарий.',
            status='published',
            parent=cls.root_comment
        )

    def test_comment_creation(self):
        """
        Проверяет корректность создания объекта Comment и его атрибутов.
        """
        comment = self.root_comment
        self.assertTrue(isinstance(comment, Comment))
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.content, 'Это корневой комментарий.')
        self.assertEqual(comment.status, 'published')
        self.assertIsNotNone(comment.time_create)
        self.assertIsNotNone(comment.time_update)
        self.assertIsNone(comment.parent)  # Корневой комментарий не имеет родителя

        # Проверка дочернего комментария
        child_comment = self.child_comment
        self.assertEqual(child_comment.parent, self.root_comment)
        self.assertEqual(child_comment.level, 1)

    def test_comment_status_choices(self):
        """
        Проверяет, что поле 'status' принимает только допустимые значения.
        """
        published_comment = Comment.objects.create(
            post=self.post, author=self.user, content='Опубликованный', status='published'
        )
        self.assertEqual(published_comment.status, 'published')

        draft_comment = Comment.objects.create(
            post=self.post, author=self.user, content='Черновик', status='draft'
        )
        self.assertEqual(draft_comment.status, 'draft')

        with self.assertRaises(ValidationError):
            invalid_status_comment = Comment(
                post=self.post, author=self.user, content='Неверный статус', status='invalid_status'
            )
            invalid_status_comment.full_clean()

    def test_comment_str_representation(self):
        """
        Проверяет корректность метода __str__.
        """
        expected_str = f'{self.root_comment.author}:{self.root_comment.content}'
        self.assertEqual(str(self.root_comment), expected_str)

    def test_comment_relationships(self):
        """
        Проверяет связи комментария с Post и User, а также древовидную структуру.
        """
        # Проверка связи Post -> Comments
        self.assertEqual(self.post.comments.count(), 2)
        self.assertIn(self.root_comment, self.post.comments.all())
        self.assertIn(self.child_comment, self.post.comments.all())

        # Проверка связи User -> Comments
        self.assertEqual(self.user.comments_author.count(), 2)
        self.assertIn(self.root_comment, self.user.comments_author.all())
        self.assertIn(self.child_comment, self.user.comments_author.all())

        # Проверка древовидной структуры (parent/children)
        self.assertEqual(self.root_comment.children.count(), 1)
        self.assertIn(self.child_comment, self.root_comment.children.all())
        self.assertIsNone(self.root_comment.parent)

        # Проверим, что при удалении родительского комментария, дочерний тоже удаляется (on_delete=models.CASCADE)
        root_comment_for_delete = Comment.objects.create(
            post=self.post, author=self.user, content='Удаляемый корень', status='published'
        )
        child_comment_for_delete = Comment.objects.create(
            post=self.post, author=self.user, content='Удаляемый дочерний', status='published',
            parent=root_comment_for_delete
        )
        self.assertTrue(Comment.objects.filter(pk=root_comment_for_delete.pk).exists())
        self.assertTrue(Comment.objects.filter(pk=child_comment_for_delete.pk).exists())

        root_comment_for_delete.delete()

        self.assertFalse(Comment.objects.filter(pk=root_comment_for_delete.pk).exists())
        self.assertFalse(Comment.objects.filter(pk=child_comment_for_delete.pk).exists())

    def test_mptt_properties(self):
        """
        Проверяет свойства MPTT-модели
        """
        # MPTT-свойства автоматически заполняются MPTT.
        self.assertIsNotNone(self.root_comment.tree_id)
        self.assertIsNotNone(self.root_comment.lft)
        self.assertIsNotNone(self.root_comment.rght)
        self.assertEqual(self.root_comment.level, 0)

        self.assertIsNotNone(self.child_comment.tree_id)
        self.assertIsNotNone(self.child_comment.lft)
        self.assertIsNotNone(self.child_comment.rght)
        self.assertEqual(self.child_comment.level, 1)

        # Убедимся, что они в одном дереве
        self.assertEqual(self.root_comment.tree_id, self.child_comment.tree_id)
        # Проверка порядка lft/rght (дочерний внутри родительского)
        self.assertTrue(self.root_comment.lft < self.child_comment.lft)
        self.assertTrue(self.root_comment.rght > self.child_comment.rght)

    def test_comment_ordering(self):
        """
        Проверяет сортировку комментариев по -time_create (от нового к старому).
        """
        # Создадим несколько комментариев для того же поста
        time.sleep(0.01)
        comment_oldest = Comment.objects.create(
            post=self.post, author=self.user, content='Самый старый', status='published'
        )
        time.sleep(0.01)
        comment_middle = Comment.objects.create(
            post=self.post, author=self.user, content='Средний', status='published'
        )
        time.sleep(0.01)
        comment_newest = Comment.objects.create(
            post=self.post, author=self.user, content='Самый новый', status='published'
        )

        all_comments = Comment.objects.filter(post=self.post).order_by('-time_create')

        self.assertEqual(len(all_comments), 5)

        self.assertEqual(all_comments[0], comment_newest)
        self.assertEqual(all_comments[1], comment_middle)
        self.assertEqual(all_comments[2], comment_oldest)
        self.assertEqual(all_comments[3], self.child_comment)
        self.assertEqual(all_comments[4], self.root_comment)


class RatingModelTest(TestCase):
    """
    Набор тестов для модели Rating.
    """

    def setUp(self):
        """
        Метод для настройки данных перед каждым тестом.
        """
        self.user1 = User.objects.create_user(username='rater_user1', password='password1')
        self.user2 = User.objects.create_user(username='rater_user2', password='password2')
        self.user_no_ratings = User.objects.create_user(username='no_ratings_user', password='password3')
        self.category = Category.objects.create(title='Тестовая Категория Рейтингов')
        self.post = Post.objects.create(
            title='Тестовый Пост Для Рейтинга',
            description='Описание.',
            text='Текст поста.',
            author=self.user1,
            category=self.category,
            status='published'
        )

        # Создаем начальные рейтинги
        self.like_rating = Rating.objects.create(
            post=self.post,
            user=self.user1,
            value=1
        )
        time.sleep(0.01)
        self.dislike_rating = Rating.objects.create(
            post=self.post,
            user=self.user2,
            value=-1
        )

    def test_rating_creation(self):
        """
        Проверяет корректность создания объекта Rating и его атрибутов.
        """
        rating = self.like_rating
        self.assertTrue(isinstance(rating, Rating))
        self.assertEqual(rating.post, self.post)
        self.assertEqual(rating.user, self.user1)
        self.assertEqual(rating.value, 1)
        self.assertIsNotNone(rating.time_create)
        self.assertEqual(str(rating), f"Рейтинг для {self.post.title} от {self.user1.username}")

        dislike_rating = self.dislike_rating
        self.assertEqual(dislike_rating.value, -1)

    def test_value_choices(self):
        """
        Проверяет, что поле 'value' принимает только допустимые значения.
        """
        with self.assertRaises(ValidationError):
            invalid_rating = Rating(
                post=self.post, user=self.user1, value=0
            )
            invalid_rating.full_clean()

        with self.assertRaises(ValidationError):
            invalid_rating = Rating(
                post=self.post, user=self.user1, value=2
            )
            invalid_rating.full_clean()

    def test_unique_together_constraint_raises_error(self):
        """
        Проверяет, что комбинация 'post' и 'user' является уникальной и
        повторная попытка создания вызывает IntegrityError.
        """
        with self.assertRaises(IntegrityError):
            Rating.objects.create(
                post=self.post,
                user=self.user1,
                value=-1
            )

    def test_unique_together_allows_other_ratings(self):
        """
        Проверяет, что уникальное ограничение позволяет создать рейтинг
        для другого поста или другим пользователем.
        """
        new_post_for_rating = Post.objects.create(
            title='Другой пост для рейтинга',
            description='desc',
            text='text',
            author=self.user1,
            category=self.category,
            status='published'
        )

        rating_by_user1_on_new_post = Rating.objects.create(
            post=new_post_for_rating,
            user=self.user1,
            value=1
        )
        self.assertIsNotNone(rating_by_user1_on_new_post.pk)

        rating_by_user2_on_new_post = Rating.objects.create(
            post=new_post_for_rating,
            user=self.user2,
            value=-1
        )
        self.assertIsNotNone(rating_by_user2_on_new_post.pk)

        new_rating_by_user_no_ratings = Rating.objects.create(
            post=self.post,
            user=self.user_no_ratings,
            value=1
        )
        self.assertIsNotNone(new_rating_by_user_no_ratings.pk)

    def test_on_delete_cascade_post(self):
        """
        Проверяет, что рейтинг удаляется при удалении связанного поста.
        """
        rating_to_delete = Rating.objects.create(
            post=self.post,
            user=self.user_no_ratings,
            value=1
        )
        self.assertTrue(Rating.objects.filter(pk=rating_to_delete.pk).exists())

        # Удаляем пост
        self.post.delete()

        # Проверяем, что рейтинг был удален
        self.assertFalse(Rating.objects.filter(pk=rating_to_delete.pk).exists())
        self.assertFalse(Rating.objects.filter(pk=self.like_rating.pk).exists())
        self.assertFalse(Rating.objects.filter(pk=self.dislike_rating.pk).exists())

    def test_on_delete_cascade_user(self):
        """
        Проверяет, что рейтинг удаляется при удалении связанного пользователя.
        """
        rating_by_user_to_delete = Rating.objects.create(
            post=self.post,
            user=self.user_no_ratings,
            value=1
        )
        self.assertTrue(Rating.objects.filter(pk=rating_by_user_to_delete.pk).exists())

        # Удаляем пользователя
        self.user_no_ratings.delete()

        # Проверяем, что рейтинг был удален
        self.assertFalse(Rating.objects.filter(pk=rating_by_user_to_delete.pk).exists())

        # Убедимся, что рейтинги других пользователей остались
        self.assertTrue(Rating.objects.filter(pk=self.like_rating.pk).exists())
        self.assertTrue(Rating.objects.filter(pk=self.dislike_rating.pk).exists())

    def test_ordering_by_time_create(self):
        """
        Проверяет сортировку рейтингов по -time_create (от нового к старому).
        """
        temp_post_for_ordering = Post.objects.create(
            title='Временный пост для теста сортировки рейтингов',
            description='desc',
            text='text',
            author=self.user1,
            category=self.category,
            status='published'
        )

        time.sleep(0.05)
        rating_for_sort_oldest = Rating.objects.create(
            post=temp_post_for_ordering, user=self.user1, value=1
        )
        time.sleep(0.05)
        rating_for_sort_middle = Rating.objects.create(
            post=temp_post_for_ordering, user=self.user2, value=-1
        )
        time.sleep(0.05)
        rating_for_sort_newest = Rating.objects.create(
            post=temp_post_for_ordering, user=self.user_no_ratings, value=1
        )

        all_ratings = Rating.objects.filter(post=temp_post_for_ordering).order_by('-time_create')

        self.assertEqual(len(all_ratings), 3)
        self.assertEqual(all_ratings[0], rating_for_sort_newest)
        self.assertEqual(all_ratings[1], rating_for_sort_middle)
        self.assertEqual(all_ratings[2], rating_for_sort_oldest)
