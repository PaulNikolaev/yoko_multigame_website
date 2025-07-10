from django.views.generic import DetailView, UpdateView, CreateView, View
from django.db import transaction
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordResetView, \
    PasswordResetConfirmView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .models import Profile
from .forms import UserUpdateForm, ProfileUpdateForm, UserRegisterForm, UserLoginForm, CustomPasswordResetForm
from cities_light.models import City, Country
from django.db.models import Q


class ProfileDetailView(DetailView):
    """
    Представление для просмотра профиля
    """
    model = Profile
    context_object_name = 'profile'
    template_name = 'accounts/profile_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Профиль пользователя: {self.object.user.username}'
        return context


class ProfileUpdateView(UpdateView):
    """
    Представление для редактирования профиля
    """
    model = Profile
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_edit.html'

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Редактирование профиля пользователя: {self.request.user.username}'
        context['slug'] = self.object.slug
        if self.request.POST:
            context['user_form'] = UserUpdateForm(self.request.POST, instance=self.request.user)
            context['form'] = self.form_class(self.request.POST, instance=self.get_object())
        else:
            context['user_form'] = UserUpdateForm(instance=self.request.user)
            context['form'] = self.form_class(instance=self.get_object())
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        with transaction.atomic():
            if all([form.is_valid(), user_form.is_valid()]):
                user_form.save()
                form.save()
            else:
                context.update({'user_form': user_form})
                return self.render_to_response(context)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('accounts:profile_detail', kwargs={'slug': self.object.slug})


class UserRegisterView(SuccessMessageMixin, CreateView):
    """
    Представление регистрации на сайте с формой регистрации
    """
    form_class = UserRegisterForm
    success_url = reverse_lazy('blog:home')
    template_name = 'accounts/user_register.html'
    success_message = 'Вы успешно зарегистрировались. Можете войти на сайт!'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Регистрация на сайте'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class UserLoginView(SuccessMessageMixin, LoginView):
    """
    Авторизация на сайте
    """
    form_class = UserLoginForm
    template_name = 'accounts/user_login.html'
    next_page = 'blog:home'
    success_message = 'Добро пожаловать на сайт!'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Авторизация на сайте'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class UserLogoutView(LogoutView):
    """
    Выход с сайта
    """
    next_page = 'blog:home'


class CustomChangePasswordView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_message = 'Вы успешно изменили пароль!'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['slug'] = self.request.user.profile.slug
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        return response

    def get_success_url(self):
        return reverse_lazy('accounts:profile_detail', kwargs={'slug': self.request.user.profile.slug})


class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    """
    Восстановление пароля с проверкой email.
    """
    form_class = CustomPasswordResetForm
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = '/accounts/password-reset/done/'
    success_message = 'Инструкции по восстановлению пароля отправлены на ваш email.'

    def get_context_data(self, **kwargs):
        """
        Добавляем данные в контекст.
        """
        context = super().get_context_data(**kwargs)
        context['title'] = 'Восстановление пароля'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class CustomPasswordResetConfirmView(SuccessMessageMixin, PasswordResetConfirmView):
    """
    Подтверждение сброса пароля
    """
    template_name = 'accounts/password_reset_confirm.html'
    success_url = '/accounts/reset/done/'
    success_message = 'Ваш пароль успешно изменен.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Установка нового пароля'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        return response


class CityAutocompleteAjaxView(View):
    def get(self, request, *args, **kwargs):
        term = request.GET.get('term', '')
        country_code = request.GET.get('country_id')

        cities = City.objects.all()

        if country_code:
            try:
                country_obj = Country.objects.get(code2=country_code)
                cities = cities.filter(country=country_obj)
            except Country.DoesNotExist:
                return JsonResponse({'results': []})
            except Exception as e:
                print(f"Ошибка при поиске страны: {e}")
                return JsonResponse({'results': []})

        cities = cities.filter(
            Q(name__icontains=term) | Q(alternate_names__icontains=term)
        ).select_related('country').order_by('name')

        results = []
        for city in cities[:50]:
            final_display_name = city.alternate_names if city.alternate_names else city.name

            results.append({
                'id': final_display_name,
                'text': final_display_name
            })

        return JsonResponse({'results': results})
