import os
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from pytils.translit import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import Profile
from apps.accounts.tests.base import AccountsBaseTest

User = get_user_model()


class ProfileModelTest(AccountsBaseTest):
    """
    Набор тестов для модели Profile.
    """

    def test_profile_creation(self):
        """Проверяет, что профиль создается автоматически при создании пользователя."""
        self.assertIsNotNone(self.profile)
        self.assertEqual(self.profile.user, self.user)
        self.assertTrue(isinstance(self.profile, Profile))

    def test_slug_generation_on_save(self):
        """
        Проверяет, что слаг генерируется из имени пользователя и является уникальным.
        """
        # 1. Проверяем, что слаг сгенерирован правильно для первого пользователя.
        self.assertIsNotNone(self.profile.slug)
        self.assertEqual(self.profile.slug, slugify(self.user.username))

        # 2. Создаем второго пользователя, чье имя при транслитерации
        conflict_username = 'test_user_accounts'
        conflict_user = User.objects.create_user(
            username=conflict_username,
            password='password123'
        )
        conflict_profile = Profile.objects.get(user=conflict_user)

        # 3. Проверяем, что слаг второго профиля уникален и имеет суффикс
        self.assertNotEqual(conflict_profile.slug, self.profile.slug)
        self.assertTrue(conflict_profile.slug.startswith(self.profile.slug))
        self.assertIn('-', conflict_profile.slug)

        # 4. Проверяем, что в базе нет двух профилей с одинаковым слагом
        self.assertEqual(Profile.objects.filter(slug=self.profile.slug).count(), 1)
