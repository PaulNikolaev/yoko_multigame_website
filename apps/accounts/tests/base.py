from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.models import Profile

User = get_user_model()


class AccountsBaseTest(TestCase):
    """
    Базовый класс для тестов приложения accounts.
    Создает пользователя и его профиль для использования во всех тестах.
    """
    @classmethod
    def setUpTestData(cls):
        # Создаем тестового пользователя
        cls.user = User.objects.create_user(
            username='testuser_accounts',
            email='test_accounts@example.com',
            password='password123'
        )

        # Профиль создается автоматически благодаря сигналу
        cls.profile = Profile.objects.get(user=cls.user)

    def setUp(self):
        super().setUp()
        self.client = self.client