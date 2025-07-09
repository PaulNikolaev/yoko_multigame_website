from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from .models import Profile
from django_countries.widgets import CountrySelectWidget
from django_select2.forms import Select2Widget
from datetime import timedelta
from django.utils import timezone


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
                                 input_formats=['%d.%m.%Y', '%Y-%m-%d'],
                                 widget=forms.DateInput(attrs={
                                     "class": "form-control mb-1 datepicker",
                                     "placeholder": "ДД.ММ.ГГГГ"
                                 }))

    class Meta:
        model = Profile
        fields = ('birth_date', 'bio', 'avatar', 'country', 'city')
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'country': CountrySelectWidget(attrs={'class': 'form-control select2-enabled'}),
            'city': Select2Widget(attrs={
                'data-placeholder': 'Начните вводить название города...',
                'class': 'form-control select2-enabled',
                'data-city-autocomplete-url': reverse_lazy('accounts:city_autocomplete_ajax')
            }),
        }
        labels = {
            'bio': 'Информация о себе',
            'avatar': 'Аватар',
            'country': 'Страна',
            'city': 'Город',
        }

    def clean_birth_date(self):
        """
        Валидация даты рождения (не должно быть будущих дат и возраст не более 90 лет)
        """
        birth_date = self.cleaned_data.get('birth_date')

        if birth_date:
            today = timezone.now().date()

            if birth_date > today:
                raise forms.ValidationError('Дата рождения не может быть в будущем.')

            check_date_for_90_years_ago = birth_date.replace(year=birth_date.year + 90)
            if check_date_for_90_years_ago < today:
                raise forms.ValidationError('Возраст не может превышать 90 лет.')

        return birth_date


class UserRegisterForm(UserCreationForm):
    """
    Переопределенная форма регистрации пользователей
    """

    class Meta(UserCreationForm.Meta):
        fields = ('username', 'password1', 'password2', 'email', 'first_name', 'last_name')

    def clean_email(self):
        """
        Проверка email на уникальность
        """
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('Такой email уже используется в системе')
        return email

    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы регистрации
        """
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({"placeholder": "Придумайте свой логин"})
        self.fields['password1'].widget.attrs.update({"placeholder": "Придумайте свой пароль"})
        self.fields['password2'].widget.attrs.update({"placeholder": "Повторите придуманный пароль"})
        self.fields['email'].widget.attrs.update({"placeholder": "Введите свой email"})
        self.fields['first_name'].widget.attrs.update({"placeholder": "Ваше имя"})
        self.fields['last_name'].widget.attrs.update({"placeholder": "Ваша фамилия"})
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": "form-control", "autocomplete": "off"})


class UserLoginForm(AuthenticationForm):
    """
    Форма авторизации на сайте
    """

    def __init__(self, *args, **kwargs):
        """
        Обновление стилей формы авторизации
        """
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Логин пользователя'
        self.fields['password'].widget.attrs['placeholder'] = 'Пароль пользователя'
        self.fields['username'].label = 'Логин'
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
            })
