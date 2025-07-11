from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from apps.services.utils import unique_slugify
from django_countries.fields import CountryField


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    slug = models.SlugField(verbose_name='URL', max_length=255, blank=True, unique=True)
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='images/avatars/%Y/%m/%d/',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=('png', 'jpg', 'jpeg'))]
    )
    bio = models.TextField(verbose_name='Информация о себе', max_length=500, blank=True, null=True)
    birth_date = models.DateField(verbose_name='Дата рождения', null=True, blank=True)
    country = CountryField(verbose_name='Страна', blank=True, null=True)
    city = models.CharField(verbose_name='Город', max_length=100, blank=True, null=True)

    class Meta:
        """
        Сортировка, название таблицы в базе данных
        """
        ordering = ('user',)
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def save(self, *args, **kwargs):
        """
        Сохранение полей модели при их отсутствии заполнения
        """
        if not self.slug:
            self.slug = unique_slugify(self, self.user.username)
        super().save(*args, **kwargs)

    def __str__(self):
        """
        Возвращение строки
        """
        return self.user.username
