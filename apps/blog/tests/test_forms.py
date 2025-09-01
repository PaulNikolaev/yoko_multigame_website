from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from ..forms import PostCreateForm, PostUpdateForm, CommentCreateForm, SearchForm
from ..models import Post, Category, Comment
from apps.blog.tests.base import BlogViewsBaseTest
User = get_user_model()


class PostCreateFormTest(BlogViewsBaseTest):
    """
    Тесты для формы PostCreateForm
    """
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

        # Проверяем, что создался новый пост
        self.assertEqual(Post.objects.count(), 3)  # Два поста уже есть в базовом классе
        created_post = Post.objects.get(title='Another Test Post')
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
        self.assertIn('test_image', post.thumbnail.name)
        post.thumbnail.delete(save=False)

    def test_form_widget_classes(self):
        """
        Тест: убедится, что стили Bootstrap применяются к виджетам формы.
        """
        form = PostCreateForm()
        for field_name, field in form.fields.items():
            if field_name != 'fixed':
                self.assertIn('form-control', field.widget.attrs.get('class', ''))
            self.assertIn('autocomplete', field.widget.attrs)
            self.assertEqual('off', field.widget.attrs.get('autocomplete'))


class PostUpdateFormTest(BlogViewsBaseTest):
    """
    Тесты для формы PostUpdateForm
    """

    def setUp(self):
        super().setUp()
        self.post_for_update = self.published_post_1

    def test_form_initial_data(self):
        """
        Тест: форма должна инициализироваться данными существующего поста.
        """
        form = PostUpdateForm(instance=self.post_for_update)
        self.assertEqual(form.initial['title'], self.post_for_update.title)
        self.assertEqual(form.initial['category'], self.post_for_update.category.pk)
        self.assertEqual(form.initial['fixed'], self.post_for_update.fixed)

    def test_form_valid_update(self):
        """
        Тест: форма должна быть валидна с корректными данными для обновления.
        """
        updated_title = 'Updated Post Title'
        updated_description = 'Updated description for the post.'
        form_data = {
            'title': updated_title,
            'category': self.category.pk,
            'description': updated_description,
            'text': self.post_for_update.text,
            'status': 'draft',
            'fixed': True,
        }
        form = PostUpdateForm(data=form_data, instance=self.post_for_update)
        self.assertTrue(form.is_valid(), f"Update Form is not valid: {form.errors}")

        updated_post = form.save()

        self.assertEqual(updated_post.pk, self.post_for_update.pk)
        self.assertEqual(updated_post.title, updated_title)
        self.assertEqual(updated_post.description, updated_description)
        self.assertEqual(updated_post.status, 'draft')
        self.assertTrue(updated_post.fixed)

    def test_form_invalid_update_missing_title(self):
        """
        Тест: форма должна быть невалидна, если обязательное поле (например, title) отсутствует при обновлении.
        """
        form_data = {
            'title': '',
            'category': self.category.pk,
            'description': 'Updated description.',
            'text': self.post_for_update.text,
            'status': 'published',
            'fixed': False,
        }
        form = PostUpdateForm(data=form_data, instance=self.post_for_update)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_form_fixed_widget_class(self):
        """
        Тест: убедится, что к виджету поля 'fixed' применен класс 'form-check-input'.
        """
        form = PostUpdateForm(instance=self.post_for_update)
        self.assertIn('form-check-input', form.fields['fixed'].widget.attrs.get('class', ''))
        self.assertIn('form-control', form.fields['title'].widget.attrs.get('class', ''))


class CommentCreateFormTest(BlogViewsBaseTest):
    """
    Тесты для формы CommentCreateForm
    """

    def test_form_valid_data(self):
        """
        Тест: форма комментария должна быть валидна с корректным содержимым.
        """
        form_data = {
            'content': 'This is a test comment content.',
        }
        form = CommentCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Comment form is not valid: {form.errors}")

    def test_form_invalid_data_empty_content(self):
        """
        Тест: форма комментария должна быть невалидна, если содержимое пустое.
        """
        form_data = {
            'content': '',
        }
        form = CommentCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)
        self.assertIn('Обязательное поле.', form.errors['content'])

    def test_form_save_comment(self):
        """
        Тест: форма должна создавать и сохранять объект Comment в базе данных.
        """
        form_data = {
            'content': 'A new comment for the post.',
        }
        form = CommentCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Comment form is not valid before save: {form.errors}")

        comment = form.save(commit=False)
        comment.author = self.user
        comment.post = self.published_post_1
        comment.save()

        self.assertEqual(Comment.objects.count(), 1)
        created_comment = Comment.objects.first()
        self.assertEqual(created_comment.content, 'A new comment for the post.')
        self.assertEqual(created_comment.author, self.user)
        self.assertEqual(created_comment.post, self.published_post_1)
        self.assertEqual(created_comment.status, 'published')

    def test_comment_form_widget_styles(self):
        """
        Тест: убедимся, что стили Bootstrap применяются к виджетам формы CommentCreateForm.
        """
        form = CommentCreateForm()
        self.assertIn('form-control', form.fields['content'].widget.attrs.get('class', ''))
        self.assertEqual('Комментарий', form.fields['content'].widget.attrs.get('placeholder'))
        self.assertEqual(5, form.fields['content'].widget.attrs.get('rows'))
        self.assertEqual(30, form.fields['content'].widget.attrs.get('cols'))


class SearchFormTest(TestCase):
    """
    Тесты для формы SearchForm
    """

    def test_form_valid_data_with_query(self):
        """
        Тест: форма поиска должна быть валидна с непустым запросом.
        """
        form_data = {
            'query': 'test search term',
        }
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Search form is not valid: {form.errors}")
        self.assertEqual(form.cleaned_data['query'], 'test search term')

    def test_form_valid_data_empty_query(self):
        """
        Тест: форма поиска должна быть валидна с пустым запросом (required=False).
        """
        form_data = {
            'query': '',
        }
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Search form with empty query is not valid: {form.errors}")
        self.assertEqual(form.cleaned_data['query'], '')

    def test_form_valid_data_no_query_field(self):
        """
        Тест: форма поиска должна быть валидна, если поле 'query' отсутствует в данных (required=False).
        """
        form_data = {}
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Search form with no query field is not valid: {form.errors}")
        self.assertEqual(form.cleaned_data['query'], '')

    def test_search_form_widget_styles(self):
        """
        Тест: убедимся, что стили Bootstrap применяются к виджетам формы SearchForm.
        """
        form = SearchForm()
        self.assertIn('form-control', form.fields['query'].widget.attrs.get('class', ''))
        self.assertEqual('Поиск статей...', form.fields['query'].widget.attrs.get('placeholder'))
