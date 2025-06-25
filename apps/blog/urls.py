from django.urls import path
from .views import (PostListView,
                    PostDetailView,
                    PostFromCategory,
                    PostCreateView)

app_name = 'blog'
urlpatterns = [
    path('', PostListView.as_view(), name='home'),
    path('post/create/', PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>', PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:slug>/', PostFromCategory.as_view(), name='post_by_category'),
]