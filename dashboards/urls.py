from django.urls import path
from . import views
# just to recommit
urlpatterns = [
    path('save/', views.save_dashboard, name='save_dashboard'),
    path('list/', views.list_dashboards, name='list_dashboards'),
    path('<int:dashboard_id>/', views.get_dashboard, name='get_dashboard'),
    path('delete/', views.delete_dashboard, name='delete_dashboard'),
    path('deploy/', views.deploy_dashboard, name='deploy_dashboard'),
]
