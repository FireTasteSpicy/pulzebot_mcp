from django.contrib import admin
from .models import UserSettings


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'allow_sentiment_analysis', 'allow_ai_analysis', 
        'allow_team_analytics', 'data_retention_days', 'updated_at'
    ]
    list_filter = [
        'allow_sentiment_analysis', 'allow_ai_analysis', 'allow_team_analytics', 
        'allow_voice_processing', 'allow_external_integrations', 
        'data_retention_days', 'github_connected', 'jira_connected', 'anonymous_mode'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Privacy & Consent', {
            'fields': (
                'allow_sentiment_analysis', 'allow_ai_analysis', 'allow_team_analytics',
                'allow_voice_processing', 'allow_external_integrations', 'anonymous_mode'
            )
        }),
        ('Data Retention', {
            'fields': ('data_retention_days',)
        }),
        ('Integration Status', {
            'fields': (
                'github_connected', 'github_integration_enabled',
                'jira_connected', 'jira_integration_enabled'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
