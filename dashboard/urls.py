from django.urls import path, include
from django.views.generic import RedirectView
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Core dashboard views
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('manager/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('export/', views.ExportReportView.as_view(), name='export'),
    
    # User settings redirects (now handled by user_settings app)
    path('user-settings/', RedirectView.as_view(pattern_name='user_settings:settings', permanent=True), name='user-settings-redirect'),
    path('settings/', RedirectView.as_view(pattern_name='user_settings:settings', permanent=True), name='settings-redirect'),
    
    # Legacy redirects
    # analysis/ redirect removed - team-health app no longer used
]
