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