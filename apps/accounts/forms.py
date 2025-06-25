from django import forms
from django.contrib.auth.models import User
from .models import Profile


class UserUpdateForm(forms.ModelForm):
    """
    Форма обновления данных пользователя
    """
    username = forms.CharField(max_length=100,
                               label='Имя пользователя',
                               widget=forms.TextInput(
                                   attrs={"class": "form-control mb-1"}))
    email = forms.EmailField(label='Email адрес', widget=forms.TextInput(attrs={"class": "form-control mb-1"}))
    first_name = forms.CharField(max_length=100,
                                 label='Имя',
                                 widget=forms.TextInput(attrs={"class": "form-control mb-1"}))
    last_name = forms.CharField(max_length=100,
                                label='Фамилия',
                                widget=forms.TextInput(attrs={"class": "form-control mb-1"}))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_email(self):
        """
        Проверка email на уникальность
        """
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Email адрес должен быть уникальным')
        return email


class ProfileUpdateForm(forms.ModelForm):
    """
    Форма обновления данных профиля пользователя
    """
    birth_date = forms.DateField(label='Дата рождения',
        widget=forms.TextInput(attrs={"class": "form-control mb-1"}))
    bio = forms.CharField(max_length=500,
                          label='Информация о себе',
                          widget=forms.Textarea(attrs={'rows': 5, "class": "form-control mb-1"}))

    avatar = forms.ImageField(label='Аватар', widget=forms.FileInput(attrs={"class": "form-control mb-1"}))
    country = forms.CharField(label='Страна', max_length=100, widget=forms.TextInput(attrs={"class": "form-control mb-1"}))
    city = forms.CharField(label='Город', max_length=100, widget=forms.TextInput(attrs={"class": "form-control mb-1"}))

    class Meta:
        model = Profile
        fields = ('birth_date', 'bio', 'avatar', 'country', 'city')