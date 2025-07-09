from django.urls import path

from .views import (ProfileUpdateView,
                    ProfileDetailView,
                    UserRegisterView,
                    UserLoginView,
                    UserLogoutView,
                    CustomChangePasswordView,
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
]
