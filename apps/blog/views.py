from django.http import JsonResponse
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from .models import Post, Category, Rating
from django.shortcuts import get_object_or_404, redirect
from .forms import PostCreateForm, PostUpdateForm, CommentCreateForm
from django.contrib.auth.mixins import LoginRequiredMixin
from ..services.mixins import AuthorRequiredMixin
from django.template.defaultfilters import date as date_filter


class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 5
    queryset = Post.custom.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Главная страница'
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.title
        context['form'] = CommentCreateForm
        return context


class PostFromCategory(ListView):
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    category = None
    paginate_by = 5

    def get_queryset(self):
        """
        Возвращает рецепты только для текущей категории.
        """
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Post.custom.filter(category=self.category)

    def get_context_data(self, **kwargs):
        """
        Добавляем название категории в контекст.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = f"Категория: {self.category.title}"
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Представление: создание материалов на сайте
    """
    model = Post
    template_name = 'blog/post_create.html'
    form_class = PostCreateForm
    login_url = 'blog:home'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавление статьи на сайт'
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'slug': self.object.slug})


class PostUpdateView(AuthorRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Представление: обновления материала на сайте
    """
    model = Post
    template_name = 'blog/post_update.html'
    context_object_name = 'post'
    form_class = PostUpdateForm
    login_url = 'blog:home'
    success_message = 'Запись была успешно обновлена!'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Обновление статьи: {self.object.title}'
        return context

    def form_valid(self, form):
        form.instance.updater = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'slug': self.object.slug})


class CommentCreateView(LoginRequiredMixin, CreateView):
    form_class = CommentCreateForm

    def is_ajax(self):
        return self.request.accepts("application/json") or self.request.headers.get(
            'X-Requested-With') == 'XMLHttpRequest'

    def form_invalid(self, form):
        if self.is_ajax():
            return JsonResponse({'error': form.errors}, status=400)
        return super().form_invalid(form)

    def form_valid(self, form):
        comment = form.save(commit=False)
        post_pk = self.kwargs.get('pk')
        try:
            post = Post.objects.get(pk=post_pk)
            comment.post = post
        except Post.DoesNotExist:
            if self.is_ajax():
                return JsonResponse({'error': 'Пост не найден.'}, status=404)
            return redirect('blog:home')
        comment.author = self.request.user
        comment.parent_id = form.cleaned_data.get('parent')
        comment.save()

        if self.is_ajax():
            profile_url = reverse('accounts:profile_detail', kwargs={'slug': comment.author.profile.slug})
            formatted_time_create = date_filter(comment.time_create, 'j F Y г. H:i')
            return JsonResponse({
                'is_child': comment.is_child_node(),
                'id': comment.id,
                'author': comment.author.username,
                'parent_id': comment.parent_id,
                'time_create': formatted_time_create,
                'avatar': comment.author.profile.avatar.url,
                'content': comment.content,
                'profile_url': profile_url
            }, status=200)

        return redirect(reverse_lazy('blog:post_detail', kwargs={'slug': comment.post.slug}))

    def handle_no_permission(self):
        if self.is_ajax():
            return JsonResponse({'error': 'Необходимо авторизоваться для добавления комментариев'}, status=400)
        return super().handle_no_permission()

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'slug': self.object.post.slug})


class RatingCreateView(LoginRequiredMixin, View):  # LoginRequiredMixin уже требует аутентификацию
    model = Rating

    def post(self, request, *args, **kwargs):
        # LoginRequiredMixin уже позаботился о неаутентифицированных пользователях,
        # так что эта проверка обычно не нужна здесь, но как страховка не помешает.
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Вы должны быть зарегистрированы, чтобы ставить оценки.'}, status=403)

        post_id = request.POST.get('post_id')
        value = int(request.POST.get('value'))

        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return JsonResponse({'error': 'Запись не найдена.'}, status=404)

        # Логика упрощается: всегда ищем по post и user, так как это unique_together
        # и пользователь всегда аутентифицирован.
        rating, created = self.model.objects.get_or_create(
            post=post,
            user=request.user,  # Теперь это наша уникальная пара
            defaults={'value': value}  # Значение для новой записи
        )

        if not created:
            # Рейтинг уже существовал для этого пользователя и поста
            if rating.value == value:
                # Если пользователь нажал ту же кнопку: отменяем голос
                rating.delete()
            else:
                # Если пользователь нажал другую кнопку: меняем голос
                rating.value = value
                rating.save()

        # Обновляем объект post, чтобы получить актуальную сумму рейтинга
        post.refresh_from_db()
        return JsonResponse({'rating_sum': post.get_sum_rating()})
