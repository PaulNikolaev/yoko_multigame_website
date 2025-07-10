from django.urls import path

from django.contrib.auth.views import PasswordResetCompleteView
from django.views.generic import TemplateView

from .views import (ProfileUpdateView,
                    ProfileDetailView,
                    UserRegisterView,
                    UserLoginView,
                    UserLogoutView,
                    CustomChangePasswordView,
                    CustomPasswordResetView,
                    CustomPasswordResetConfirmView,
                    CityAutocompleteAjaxView)

app_name = 'accounts'

urlpatterns = [
    path('user/<slug:slug>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('user/<slug:slug>/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('user/<slug:slug>/password_change/', CustomChangePasswordView.as_view(), name='password_change'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('city-autocomplete/', CityAutocompleteAjaxView.as_view(), name='city_autocomplete_ajax'),

    #   Восстановление пароля
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', TemplateView.as_view(template_name='accounts/password_reset/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='accounts/password_reset/password_reset_complete.html'),
         name='password_reset_complete'),
]
