from django.contrib import admin
from .models import Post, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Админ-панель модели категорий
    """
    prepopulated_fields = {"slug": ("title",)}


admin.site.register(Post)
