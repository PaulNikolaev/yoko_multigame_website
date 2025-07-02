from django.db import models
from django.db.models import Sum
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from apps.services.utils import unique_slugify


class PostManager(models.Manager):
    """
    Кастомный менеджер для модели постов
    """

    def get_queryset(self):
        """
        Список постов (SQL запрос с фильтрацией по статусу опубликованно)
        """
        return super().get_queryset().select_related('author', 'category').filter(status='published')


class Post(models.Model):
    """
    Модель постов для сайта
    """
    STATUS_OPTIONS = (
        ('published', 'Опубликовано'),
        ('draft', 'Черновик')
    )

    title = models.CharField(verbose_name='Название записи', max_length=255)
    slug = models.SlugField(verbose_name='URL', max_length=255, blank=True)
    description = models.TextField(verbose_name='Краткое описание', max_length=500)
    text = models.TextField(verbose_name='Полный текст записи')
    category = models.ForeignKey(
        'Category',
        verbose_name='Категория',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts'
    )
    thumbnail = models.ImageField(
        default='images/thumbnails/default.jpg',
        verbose_name='Изображение записи',
        blank=True,
        upload_to='images/thumbnails/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=('png', 'jpg', 'webp', 'jpeg', 'gif'))]
    )
    status = models.CharField(choices=STATUS_OPTIONS, default='published', verbose_name='Статус записи', max_length=10)
    create = models.DateTimeField(verbose_name='Время добавления', auto_now_add=True)
    update = models.DateTimeField(verbose_name='Время изменения', auto_now=True)
    author = models.ForeignKey(to=User, verbose_name='Автор', on_delete=models.SET_DEFAULT, related_name='author_posts',
                               default=1)
    updater = models.ForeignKey(to=User, verbose_name='Обновил', on_delete=models.SET_NULL, null=True,
                                related_name='updater_posts', blank=True)
    fixed = models.BooleanField(verbose_name='Прикреплено', default=False)
    objects = models.Manager()
    custom = PostManager()

    class Meta:
        db_table = 'blog_post'
        ordering = ['-fixed', '-create']
        indexes = [models.Index(fields=['-fixed', '-create', '-status'])]
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        При сохранении генерируем слаг и проверяем на уникальность
        """
        self.slug = unique_slugify(self, self.title)
        super().save(*args, **kwargs)

    def get_sum_rating(self):
        return self.rating.aggregate(total_rating=Sum('value'))['total_rating'] or 0


class Category(models.Model):
    """
    Категории статей
    """
    title = models.CharField(max_length=255, verbose_name='Название категории')
    slug = models.SlugField(max_length=255, verbose_name='URL категории', blank=True)
    description = models.TextField(verbose_name='Описание категории',
                                   max_length=300,
                                   blank=True,
                                   null=True,
                                   default='Нет описания')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        """
        Возвращение заголовка категории
        """
        return self.title


class Comment(MPTTModel):
    """
    Модель древовидных комментариев
    """
    STATUS_OPTIONS = (
        ('published', 'Опубликовано'),
        ('draft', 'Черновик')
    )
    post = models.ForeignKey(Post, verbose_name='Запись', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, verbose_name='Автор комментария', on_delete=models.CASCADE,
                               related_name='comments_author')
    content = models.TextField(verbose_name='Текст комментария', max_length=3000)
    time_create = models.DateTimeField(verbose_name='Время добавление', auto_now_add=True)
    time_update = models.DateTimeField(verbose_name='Время изменения', auto_now=True)
    status = models.CharField(choices=STATUS_OPTIONS, default='published', verbose_name='Статус комментария',
                              max_length=10)
    parent = TreeForeignKey('self', verbose_name='Родительский комментарий', null=True, blank=True,
                            related_name='children', on_delete=models.CASCADE)

    class MPTTMeta:
        """
        Сортировка по вложенности
        """
        order_insertion_by = ('-time_create',)

    class Meta:
        """
        Сортировка, название модели в админ панели, таблица в данными
        """
        ordering = ['-time_create']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'{self.author}:{self.content}'


class Rating(models.Model):
    """
    Модель рейтинга: Лайк - Дизлайк
    """
    post = models.ForeignKey(to=Post, verbose_name='Запись', on_delete=models.CASCADE, related_name='rating')
    user = models.ForeignKey(to=User, verbose_name='Пользователь', on_delete=models.CASCADE, blank=True, null=True)
    value = models.IntegerField(verbose_name='Значение', choices=[(1, 'Нравится'), (-1, 'Не нравится')])
    time_create = models.DateTimeField(verbose_name='Время добавления', auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')
        ordering = ('-time_create',)
        indexes = [models.Index(fields=['time_create', 'value'])]
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтинги'

    def __str__(self):
        return f"Рейтинг для {self.post.title} от {self.user.username}"
