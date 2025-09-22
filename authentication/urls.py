"""
Authentication URLs
"""

from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('redirect/', views.RoleBasedRedirectView.as_view(), name='role_redirect'),
    path('access-denied/', views.access_denied_view, name='access_denied'),
]
