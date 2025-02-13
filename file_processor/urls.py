from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),  # URL for uploading files
    path('fetch_files/', views.fetch_files, name='fetch_files'),  # URL for fetching and parsing CSV
]
