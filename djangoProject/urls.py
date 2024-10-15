from django.contrib import admin
from django.urls import path, include 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('login_service.urls')), 
    path('file/', include('file_processor.urls')), 
]