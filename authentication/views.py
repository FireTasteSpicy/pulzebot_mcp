"""
Authentication views for user login/logout and role-based routing.

This module provides:
- Custom login view with role-based redirection
- Logout functionality with session cleanup
- Role-based dashboard routing based on user profiles
- Access denied handling for unauthorized access
"""

from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.urls import reverse
from django.contrib import messages
import logging

try:
    from dashboard.models import UserProfile
except ImportError:
    UserProfile = None

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    """
    Custom login view that extends Django's built-in LoginView.
    """
    template_name = 'authentication/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect to role-based redirect view after successful login."""
        return reverse('authentication:role_redirect')
    
    def form_invalid(self, form):
        """Handle failed authentication with user-friendly message."""
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)


def custom_logout_view(request):
    """
    Custom logout view that logs out the user and redirects to login.
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        logger.info(f"User {username} logged out")
    return redirect('authentication:login')


class RoleBasedRedirectView(TemplateView):
    """
    View to redirect users to appropriate dashboard based on their role.    
    Used as the default login redirect destination.
    """
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('authentication:login')
        
        try:
            if UserProfile:
                profile = UserProfile.objects.get(user=request.user)
                if profile.is_manager:
                    return redirect('dashboard:manager_dashboard')
                else:
                    return redirect('dashboard:dashboard')
            else:
                # If UserProfile model not available, redirect to dashboard
                return redirect('dashboard:dashboard')
                
        except UserProfile.DoesNotExist:
            # Create developer profile and redirect to normal dashboard
            if UserProfile:
                UserProfile.objects.create(user=request.user, role='developer')
                logger.info(f"Created developer profile for user {request.user.username}")
            return redirect('dashboard:dashboard')


def access_denied_view(request):
    """
    View for when users don't have sufficient permissions.
    """
    context = {
        'title': 'Access Denied',
        'message': 'You do not have permission to access this resource.'
    }
    return render(request, 'authentication/access_denied.html', context)
