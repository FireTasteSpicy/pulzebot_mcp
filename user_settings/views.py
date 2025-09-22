from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import UserSettings
from .forms import UserSettingsForm, UserProfileForm
from .privacy_service import PrivacyEnforcementService


@login_required
def user_settings_view(request):
    """
    Simplified User Settings page for MVP - basic privacy preferences and app settings.
    """
    # Get or create user settings
    user_settings, created = UserSettings.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        settings_form = UserSettingsForm(request.POST, instance=user_settings)
        profile_form = UserProfileForm(request.POST, instance=request.user)
        
        if settings_form.is_valid() and profile_form.is_valid():
            settings_form.save()
            profile_form.save()
            
            messages.success(request, 'Your settings have been updated successfully.')
            return redirect('user_settings:settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        settings_form = UserSettingsForm(instance=user_settings)
        profile_form = UserProfileForm(instance=request.user)
    
    # Get privacy status for display
    privacy_status = PrivacyEnforcementService.get_user_privacy_status(request.user)
    processing_summary = PrivacyEnforcementService.get_processing_summary(request.user)
    
    context = {
        'settings_form': settings_form,
        'profile_form': profile_form,
        'user_settings': user_settings,
        'privacy_status': privacy_status,
        'processing_summary': processing_summary,
    }
    
    return render(request, 'user_settings/settings.html', context)


@login_required
def data_export_view(request):
    """
    Simple data export for transparency (MVP version).
    """
    user_data = {
        'profile': {
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'date_joined': request.user.date_joined.isoformat(),
        },
        'settings': {},
    }
    
    # Add user settings
    try:
        user_settings = UserSettings.objects.get(user=request.user)
        user_data['settings'] = {
            # Essential settings data only
            'data_retention_days': user_settings.data_retention_days,
            'allow_sentiment_analysis': user_settings.allow_sentiment_analysis,
            'allow_ai_analysis': user_settings.allow_ai_analysis,
            'allow_team_analytics': user_settings.allow_team_analytics,
            'allow_voice_processing': user_settings.allow_voice_processing,
            'allow_external_integrations': user_settings.allow_external_integrations,
            'anonymous_mode': user_settings.anonymous_mode,
            'github_connected': user_settings.github_connected,
            'github_integration_enabled': user_settings.github_integration_enabled,
            'jira_connected': user_settings.jira_connected,
            'jira_integration_enabled': user_settings.jira_integration_enabled,
        }
    except UserSettings.DoesNotExist:
        pass
    
    json_data = json.dumps(user_data, indent=2)
    response = HttpResponse(json_data, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="pulzebot_data_{request.user.username}.json"'
    return response


@login_required
@require_http_methods(["POST"])
def revoke_ai_consent_view(request):
    """
    Quickly disable all AI processing for privacy-conscious users.
    """
    try:
        user_settings = UserSettings.objects.get(user=request.user)
        
        # Disable AI processing
        user_settings.allow_sentiment_analysis = False
        user_settings.allow_ai_analysis = False
        user_settings.allow_team_analytics = False
        user_settings.allow_voice_processing = False
        user_settings.save()
        
        return JsonResponse({'success': True, 'message': 'AI processing disabled successfully.'})
    except UserSettings.DoesNotExist:
        return JsonResponse({'error': 'User settings not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def save_integrations_view(request):
    """
    Save integration settings for the user.
    """
    try:
        data = json.loads(request.body)
        
        # Update user settings with integration status
        user_settings, created = UserSettings.objects.get_or_create(user=request.user)
        
        # Save Jira integration status
        if 'jira' in data:
            jira_data = data['jira']
            user_settings.jira_integration_enabled = jira_data.get('enabled', False)
            user_settings.jira_connected = jira_data.get('connected', False)
        
        # Save GitHub integration status
        if 'github' in data:
            github_data = data['github']
            user_settings.github_integration_enabled = github_data.get('enabled', False)
            user_settings.github_connected = github_data.get('connected', False)
        
        user_settings.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required 
def check_consent_api(request):
    """
    API endpoint to check user consent for specific operations.
    """
    operation_type = request.GET.get('operation')
    
    if not operation_type:
        return JsonResponse({
            'error': 'operation parameter required'
        }, status=400)
    
    consent_given, message = PrivacyEnforcementService.check_processing_consent(
        request.user, operation_type
    )
    
    return JsonResponse({
        'operation': operation_type,
        'consent_given': consent_given,
        'message': message
    })
