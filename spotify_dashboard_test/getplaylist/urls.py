from django.urls import path
from . import views

urlpatterns = [
    path('getplaylist/login', views.start_login, name='login'),
    path('getplaylist/login_callback', views.end_login, name='login_callback'),
    path('getplaylist/get', views.get_playlists, name='get_playlists'),
]