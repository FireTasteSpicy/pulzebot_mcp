"""
URL configuration for pulzebot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.views.generic import RedirectView
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from dashboard.views import health_check, liveness_probe, readiness_probe, metrics

def root_redirect(request):
    """Redirect root based on authentication status."""
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')
    else:
        return redirect('authentication:login')

def chrome_devtools_handler(request):
    """Handle Chrome DevTools requests to eliminate 404 warnings."""
    return JsonResponse({}, status=204)  # No Content

urlpatterns = [
    # Root and administrative routes
    path('', root_redirect, name='root'),
    path('admin/', admin.site.urls),
    path('auth/', include((
        'authentication.urls', 'authentication'
    ), namespace='authentication')),
    
    # Core application routes
    path('dashboard/', include((
        'dashboard.urls', 'dashboard'
    ), namespace='dashboard')),
    
    # Feature-specific applications  
    path('standup/', include((
        'standup.urls', 'standup'
    ), namespace='standup')),

    # Redirect integrations to settings page (consolidated)
    path('integrations/', RedirectView.as_view(pattern_name='user_settings:settings', permanent=True), name='integrations_redirect'),
    
    # Keep API endpoints for integration functionality
    path('integrations/api/', include((
        'integrations.urls', 'integrations'
    ), namespace='integrations')),
    path('settings/', include((
        'user_settings.urls', 'user_settings'
    ), namespace='user_settings')),
    
    # API routes (versioned)
    path('api/v1/ai/', include((
        'ai_processing.urls', 'ai_processing'
    ), namespace='ai_processing')),
    
    # System and monitoring routes
    path('health/', health_check, name='health_check'),
    path('health/live/', liveness_probe, name='liveness_probe'),
    path('health/ready/', readiness_probe, name='readiness_probe'),
    path('metrics/', metrics, name='metrics'),
    
    # Development and debugging routes
    path('.well-known/appspecific/com.chrome.devtools.json', chrome_devtools_handler, name='chrome_devtools'),
    
    # Legacy redirects for backward compatibility
    path('dashboard/user-settings/', RedirectView.as_view(pattern_name='user_settings:settings', permanent=True), name='old_user_settings_redirect'),
    path('api/ai/', RedirectView.as_view(pattern_name='ai_processing:process_standup', permanent=True), name='old_ai_redirect'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
