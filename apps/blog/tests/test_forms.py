from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..forms import PostCreateForm
from ..models import Post, Category, Comment

User = get_user_model()


class PostCreateFormTest(TestCase):
    """
    Тесты для формы PostCreateForm
    """

    @classmethod
    def setUpTestData(cls):
        """
        Настройка данных, которые будут использоваться всеми тестовыми методами класса.
        Выполняется один раз для всего класса.
        """
        cls.user = User.objects.create_user(username='testuser', password='password123')
        cls.category = Category.objects.create(title='Test Category', slug='test-category')

    def test_form_valid_data(self):
        """
        Тест: форма должна быть валидна с корректными данными.
        """
        form_data = {
            'title': 'Test Post Title',
            'category': self.category.pk,
            'description': 'This is a test post description.',
            'text': 'This is the full text of the test post.',
            'status': 'published',
        }
        form = PostCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form is not valid: {form.errors}")

    def test_form_invalid_data_missing_title(self):
        """
        Тест: форма должна быть невалидна, если отсутствует обязательное поле 'title'.
        """
        form_data = {
            'category': self.category.pk,
            'description': 'This is a test post description.',
            'text': 'This is the full text of the test post.',
            'status': 'published',
        }
        form = PostCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_form_invalid_data_missing_description(self):
        """
        Тест: форма должна быть невалидна, если отсутствует обязательное поле 'description'.
        """
        form_data = {
            'title': 'Test Post Title',
            'category': self.category.pk,
            'text': 'This is the full text of the test post.',
            'status': 'published',
        }
        form = PostCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('description', form.errors)

    def test_form_save(self):
        """
        Тест: форма должна создавать и сохранять объект Post в базе данных.
        """
        form_data = {
            'title': 'Another Test Post',
            'category': self.category.pk,
            'description': 'Another description.',
            'text': 'Another full text.',
            'status': 'draft',
        }
        form = PostCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form is not valid before save: {form.errors}")

        post = form.save(commit=False)
        post.author = self.user
        post.save()

        self.assertEqual(Post.objects.count(), 1)
        created_post = Post.objects.first()
        self.assertEqual(created_post.title, 'Another Test Post')
        self.assertEqual(created_post.author, self.user)
        self.assertEqual(created_post.category, self.category)
        self.assertEqual(created_post.status, 'draft')

    def test_form_thumbnail_upload(self):
        """
        Тест: форма должна обрабатывать загрузку миниатюры.
        """
        image_content = b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
        thumbnail_file = SimpleUploadedFile(
            "test_image.gif",
            image_content,
            content_type="image/gif"
        )

        form_data = {
            'title': 'Post with Image',
            'category': self.category.pk,
            'description': 'Description with image.',
            'text': 'Text with image.',
            'status': 'published',
        }
        file_data = {'thumbnail': thumbnail_file}

        form = PostCreateForm(data=form_data, files=file_data)
        self.assertTrue(form.is_valid(), f"Form with image is not valid: {form.errors}")

        post = form.save(commit=False)
        post.author = self.user
        post.save()

        self.assertIsNotNone(post.thumbnail)
        self.assertTrue(post.thumbnail.name.endswith('test_image.gif'))
        post.thumbnail.delete(save=False)