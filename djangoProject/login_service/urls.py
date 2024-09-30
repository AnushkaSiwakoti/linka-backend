from django.urls import path
from . import views

urlpatterns = [
    path('create-account/', views.create_Account, name='create_account'),
    path('verify-account/', views.verify_Account, name='verify_account'),
    path('', views.get_routes),
]
