from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('for-you/', views.for_you, name='for_you'),
    path('book/<slug:book_id>/', views.book_detail, name='book_detail'),
    path('choose-plan/', views.choose_plan, name='choose_plan'),
    path('player/<slug:book_id>/', views.player, name='player'),
    path('auth/', views.handle_auth, name='handle_auth'),
    path('logout/', views.logout_user, name='logout_user'),
    path('settings/', views.settings, name='settings'),
    path('library/', views.library, name='library'),
    path('save-book/<slug:book_id>/', views.save_book, name='save_book'),
    path('search/', views.search, name='search'),
]
