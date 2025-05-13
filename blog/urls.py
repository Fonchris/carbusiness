

from .views import AddCommentView, FeedView, HomeView,AddPostView,ArticleDetailView,UpdatePostView,DeletePostView,LikeView,AddCategoryView,CategoryView,CategoryListView, UserPostsView, announcements, get_notifications, get_unread_count, mark_notification_read, posts,search, handle_dropdown,artsanddesign,  track_post_view
from django.urls import path


urlpatterns = [
    # path('',views.home, name="home"),
    path('', HomeView.as_view(), name="home"),
    path('article/<int:pk>/', ArticleDetailView.as_view(), name='article-detail'),
    path('add_post/', AddPostView.as_view(), name="add_post"),
    path('article/<int:pk>/comment/', AddCommentView.as_view(), name="add_comment"),
    path('add_category/', AddCategoryView.as_view(), name="add_category"),
    path('article/edit/<int:pk>', UpdatePostView.as_view(), name="edit_post"),
    path('article/<int:pk>/delete', DeletePostView.as_view(), name="delete_post"),
    path('category/<str:cats>/', CategoryView, name='category',),
    path('categories_list/', CategoryListView, name='categories_list',),
    path('like/<int:pk>', LikeView,name="like_post"),
    path('search/', search,name="search"),
    path('handle_dropdown/', handle_dropdown, name='handle_dropdown'),
    path('artsanddesign/', artsanddesign, name='artsanddesign'),
    path('posts/', posts, name='posts'),
    path('announcements/', announcements, name='announcements'),
    path('user/<int:user_id>/posts/', UserPostsView.as_view(), name="user_posts"),
    path('notifications/', get_notifications, name='get_notifications'),
    path('notifications/unread_count/', get_unread_count, name='unread_count'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('feed/', FeedView.as_view(), name='feed'),
    path('track-view/<int:pk>/', track_post_view, name='track_post_view'),
]
