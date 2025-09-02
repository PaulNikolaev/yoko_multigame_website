import os
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
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
