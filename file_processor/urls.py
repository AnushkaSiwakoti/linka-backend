# file_processor/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),
    path('fetch_file/', views.fetch_file, name='fetch_file'),
]