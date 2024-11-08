from django.urls import path
from . import views

urlpatterns = [
    path('create-account/', views.create_Account, name='create-account'),
    path('verify-account/', views.verify_Account, name='verify-account'),
    
]
