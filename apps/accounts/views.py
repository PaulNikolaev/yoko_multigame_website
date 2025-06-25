from django.views.generic import DetailView, UpdateView
from django.db import transaction
from django.urls import reverse_lazy

from .models import Profile
from .forms import UserUpdateForm, ProfileUpdateForm


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

        if all([form.is_valid(), user_form.is_valid()]):
            with transaction.atomic():
                user_form.save()
                form.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(context)

    def get_success_url(self):
        return reverse_lazy('accounts:profile_detail', kwargs={'slug': self.object.slug})
