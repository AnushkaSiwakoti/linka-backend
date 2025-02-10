# recommit
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

# Define any root views or include URLs from your apps
urlpatterns = [
    path('admin/', admin.site.urls),                    # Admin interface
    path('', include('login_service.urls')),            # Root URL routes to login_service
    path('file/', include('file_processor.urls')),      # File processing app URL
    path('dashboards/', include('dashboards.urls')),
    
]
