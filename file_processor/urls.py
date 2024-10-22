from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),  # URL for uploading files
    path('fetch_csv/', views.fetch_csv, name='fetch_csv'),  # URL for fetching and parsing CSV
]
