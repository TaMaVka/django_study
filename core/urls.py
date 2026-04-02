"""URL configuration for core application."""

from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('theory/', views.theory_list, name='theory_list'),
    path('theory/<int:pk>/', views.theory_detail, name='theory_detail'),
    path('theory/submit/', views.theory_submit, name='theory_submit'),
    path('play/hex/', views.hex_game, name='hex_game'),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='core/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register_view, name='register'),
]