import os
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from pytils.translit import slugify
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.utils import DataError
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

    def test_avatar_upload(self):
        """Проверяет загрузку и сохранение файла аватара."""
        # Создаем тестовый PNG-файл, так как GIF не поддерживается
        png_content = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4'
            b'\x89\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\x97y\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        uploaded_image = SimpleUploadedFile(
            name='test_avatar.png',
            content=png_content,
            content_type='image/png'
        )

        self.profile.avatar = uploaded_image
        self.profile.full_clean()
        self.profile.save()

        # Проверяем, что файл был загружен в правильную директорию
        self.assertTrue(self.profile.avatar.name.startswith('images/avatars/'))
        self.assertIn('test_avatar.png', self.profile.avatar.name)

        # Удаляем файл после теста, чтобы не засорять медиа-папку
        if os.path.exists(self.profile.avatar.path):
            os.remove(self.profile.avatar.path)

    def test_avatar_file_extension_validator(self):
        """Проверяет, что валидатор FileExtensionValidator работает корректно."""
        text_file = SimpleUploadedFile(
            name='test.txt',
            content=b'some text',
            content_type='text/plain'
        )

        # Попытка присвоить файл с некорректным расширением должна вызвать ValidationError
        with self.assertRaises(ValidationError):
            self.profile.avatar = text_file
            self.profile.full_clean()

    def test_profile_bio_max_length(self):
        """Проверяет, что поле bio не превышает максимальную длину, используя full_clean()."""
        long_bio = 'a' * 501  # Строка, превышающая 500 символов
        self.profile.bio = long_bio

        with self.assertRaises(ValidationError) as cm:
            self.profile.full_clean()

        # Дополнительная проверка, чтобы убедиться, что ошибка связана именно с полем bio
        self.assertIn('bio', cm.exception.message_dict)
