from django.http import JsonResponse
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View, FormView
from .models import Post, Category, Rating, Comment
from django.shortcuts import get_object_or_404, redirect, render
from .forms import PostCreateForm, PostUpdateForm, CommentCreateForm, SearchForm
from django.contrib.auth.mixins import LoginRequiredMixin
from ..services.mixins import AuthorRequiredMixin
from django.template.loader import render_to_string
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value
from django.db.models.functions import Lower


class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 5
    queryset = Post.custom.published()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Главная страница'
        return context


class UserPostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'blog/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        return Post.custom.published().filter(author=self.request.user).order_by('-create')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Мои статьи'
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.custom.published()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.title
        context['form'] = CommentCreateForm()
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
        return Post.custom.published().filter(category=self.category)

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
    login_url = 'blog:home'
    form_class = CommentCreateForm
    template_name = 'blog/post_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post_pk = self.kwargs.get('pk')
        try:
            post = get_object_or_404(Post, pk=post_pk)
            context['post'] = post
        except Exception:
            pass
        return context

    def get_permission_denied_url(self):
        return self.login_url

    def is_ajax(self):
        return self.request.accepts("application/json") or self.request.headers.get(
            'X-Requested-With') == 'XMLHttpRequest'

    def form_invalid(self, form):
        if self.is_ajax():
            return JsonResponse({'success': False, 'errors': form.errors.as_json()}, status=400)
        return super().form_invalid(form)

    def form_valid(self, form):
        print("Вход в form_valid")
        comment = form.save(commit=False)
        post_pk = self.kwargs.get('pk')
        try:
            post = get_object_or_404(Post, pk=post_pk)
            comment.post = post
        except Exception:
            if self.is_ajax():
                return JsonResponse({'success': False, 'error': 'Пост не найден.'}, status=404)
            return redirect('blog:home')

        comment.author = self.request.user

        parent_id = form.cleaned_data.get('parent')
        if parent_id:
            try:
                comment.parent = Comment.objects.get(pk=parent_id)
            except Comment.DoesNotExist:
                comment.parent = None

        comment.save()

        comment.refresh_from_db()

        if self.is_ajax():
            print("Это AJAX-запрос")
            comment_html = render_to_string(
                'blog/comments/single_comment_node.html',
                {'node': comment, 'request': self.request},
            )
            return JsonResponse({'success': True, 'comment_html': comment_html}, status=200)
        else:
            print("Это обычный запрос. Ожидаем перенаправление.")
        return redirect(reverse_lazy('blog:post_detail', kwargs={'slug': comment.post.slug}))

    def handle_no_permission(self):
        if self.is_ajax():
            return JsonResponse({'success': False, 'error': 'Необходимо авторизоваться для добавления комментариев.'},
                                status=403)
        return super().handle_no_permission()

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={'slug': self.object.post.slug})


class RatingCreateView(LoginRequiredMixin, View):
    model = Rating

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Вы должны быть зарегистрированы, чтобы ставить оценки.'}, status=403)

        post_id = request.POST.get('post_id')
        value = int(request.POST.get('value'))

        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return JsonResponse({'error': 'Запись не найдена.'}, status=404)

        rating, created = self.model.objects.get_or_create(
            post=post,
            user=request.user,
            defaults={'value': value}
        )

        if not created:
            if rating.value == value:
                rating.delete()
            else:
                rating.value = value
                rating.save()

        post.refresh_from_db()
        return JsonResponse({'rating_sum': post.get_sum_rating()})


class PostSearchView(ListView):
    model = Post
    template_name = 'blog/post_search.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        form = SearchForm(self.request.GET)
        query = None
        results = Post.objects.none()

        if form.is_valid():
            query = form.cleaned_data['query']

            if query:
                lower_query_value = Value(query.lower())

                SIMILARITY_THRESHOLD = 0.1

                results = Post.custom.published().annotate(
                    similarity=TrigramSimilarity(Lower('title'), lower_query_value)
                ).filter(similarity__gt=SIMILARITY_THRESHOLD).order_by("-similarity")

        self.query = query
        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Результаты поиска'
        context["search_form"] = SearchForm(self.request.GET)
        context['query'] = self.query
        return context


def tr_handler404(request, exception):
    """
    Обработка ошибки 404
    """
    return render(request=request, template_name='errors/error_page.html', status=404, context={
        'title': 'Страница не найдена: 404',
        'error_message': 'К сожалению такая страница была не найдена, или перемещена',
    })


def tr_handler500(request):
    """
    Обработка ошибки 500
    """
    return render(request=request, template_name='errors/error_page.html', status=500, context={
        'title': 'Ошибка сервера: 500',
        'error_message': 'Внутренняя ошибка сайта, вернитесь на главную страницу, отчёт об ошибке мы направим администрации сайта',
    })


def tr_handler403(request, exception):
    """
    Обработка ошибки 403
    """
    return render(request=request, template_name='errors/error_page.html', status=403, context={
        'title': 'Ошибка доступа: 403',
        'error_message': 'Доступ к этой странице ограничен',
    })
