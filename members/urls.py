from django.urls import path
from . import views

urlpatterns = [
    path('signup', views.signup, name='signup'),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('get_started', views.get_started, name='get_started'),
    path('signin', views.signin, name='signin'),
    path('signout', views.signout, name='signout'),
    path('terms_and_conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('edit_profile', views.edit_profile, name='edit_profile'),
    path('<int:pk>/profile', views.ShowProfilePageView.as_view(), name='show_profile_page'),
    path('<int:pk>/edit_profile_page', views.EditProfilePageView.as_view(), name='edit_profile_page'),
    path('create_profile_page', views.CreateProfilePageView.as_view(), name='create_profile_page'),
    path('contact/', views.contact, name='contact'),
    path('contact/success/', views.contact_success, name='contact_success'),
    path('follow/<int:pk>/', views.FollowUserView.as_view(), name='follow_user'),
    path('unfollow/<int:pk>/', views.UnfollowUserView.as_view(), name='unfollow_user'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('followers/<int:pk>/', views.FollowersListView.as_view(), name='followers_list'),
    path('following/<int:pk>/', views.FollowingListView.as_view(), name='following_list'),
]
