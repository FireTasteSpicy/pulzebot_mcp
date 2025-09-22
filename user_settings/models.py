from django.db import models
from django.contrib.auth.models import User


class UserSettings(models.Model):
    """
    Streamlined User Settings model for essential privacy and integration controls.
    Focused on MVP features that are actually used in the application.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Core Data Privacy Controls
    DATA_RETENTION_CHOICES = [
        (30, '30 days'),
        (60, '60 days'), 
        (90, '90 days'),
    ]
    data_retention_days = models.IntegerField(
        choices=DATA_RETENTION_CHOICES,
        default=90,
        help_text="Automatically delete my data after specified days"
    )
    
    # Essential Privacy Consent 
    allow_sentiment_analysis = models.BooleanField(
        default=True,
        help_text="Enable AI sentiment analysis of my standup submissions"
    )
    allow_ai_analysis = models.BooleanField(
        default=True,
        help_text="Allow AI analysis of standup data for insights and summaries"
    )
    allow_team_analytics = models.BooleanField(
        default=True,
        help_text="Include my data in team-wide analytics and insights"
    )
    allow_voice_processing = models.BooleanField(
        default=False,
        help_text="Allow voice input processing and transcription"
    )
    allow_external_integrations = models.BooleanField(
        default=True,
        help_text="Allow integration with external tools (GitHub, Jira)"
    )
    
    # Privacy Protection
    anonymous_mode = models.BooleanField(
        default=False,
        help_text="Hide identifying information in team analytics"
    )
    
    # Integration Status (managed by frontend)
    github_connected = models.BooleanField(
        default=False,
        help_text="GitHub integration connection status"
    )
    github_integration_enabled = models.BooleanField(
        default=False,
        help_text="Enable GitHub integration for work item tracking"
    )
    jira_connected = models.BooleanField(
        default=False,
        help_text="Jira integration connection status"
    )
    jira_integration_enabled = models.BooleanField(
        default=False,
        help_text="Enable Jira integration for work item tracking"
    )
    
    # Account Management
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'
    
    def __str__(self):
        return f"Settings for {self.user.username}"
