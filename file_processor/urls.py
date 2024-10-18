from django.urls import path
from .views import upload_file
from . import views

urlpatterns = [
    path('upload/', views.upload_file, name='upload_file'),  # URL for uploading files
]