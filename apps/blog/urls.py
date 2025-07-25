from django.urls import path
from .views import (PostListView,
                    UserPostListView,
                    PostDetailView,
                    PostFromCategory,
                    PostCreateView,
                    PostUpdateView,
                    CommentCreateView,
                    RatingCreateView,
                    PostSearchView)

app_name = 'blog'
urlpatterns = [
    path('', PostListView.as_view(), name='home'),
    path('post/create/', PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/update/', PostUpdateView.as_view(), name='post_update'),
    path('post/<slug:slug>', PostDetailView.as_view(), name='post_detail'),
    path('post/<int:pk>/comments/create/', CommentCreateView.as_view(), name='comment_create_view'),
    path('category/<slug:slug>/', PostFromCategory.as_view(), name='post_by_category'),
    path('rating/', RatingCreateView.as_view(), name='rating'),
    path('search/', PostSearchView.as_view(), name='post_search'),
    path('my-posts/', UserPostListView.as_view(), name='my_posts')
]
