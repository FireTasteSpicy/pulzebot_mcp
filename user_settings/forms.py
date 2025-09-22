from django import forms
from django.contrib.auth.models import User
from .models import UserSettings


class UserSettingsForm(forms.ModelForm):
    """
    Simplified User Settings form for MVP - basic privacy and preferences.
    """
    class Meta:
        model = UserSettings
        fields = [
            'data_retention_days',
            'allow_sentiment_analysis',
            'allow_ai_analysis',
            'allow_team_analytics',
            'allow_voice_processing',
            'allow_external_integrations',
            'anonymous_mode',
        ]
        
        widgets = {
            'data_retention_days': forms.Select(attrs={
                'class': 'form-select',
                'title': 'How long to keep your data before automatic deletion'
            }),
            'allow_sentiment_analysis': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'title': 'Enable AI sentiment analysis of your standup submissions'
            }),
            'allow_ai_analysis': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'title': 'Allow AI analysis of standup data for insights and summaries'
            }),
            'allow_team_analytics': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'title': 'Include your data in team-wide analytics and insights'
            }),
            'allow_voice_processing': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'title': 'Allow voice input processing and transcription'
            }),
            'allow_external_integrations': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'title': 'Allow integration with external tools (GitHub, Jira)'
            }),
            'anonymous_mode': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'title': 'Hide identifying information in team analytics'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Group fields for better organization in templates
        self.privacy_fields = [
            'allow_sentiment_analysis',
            'allow_ai_analysis', 
            'allow_team_analytics',
            'allow_voice_processing',
            'allow_external_integrations',
            'anonymous_mode',
        ]
        
        self.data_retention_fields = [
            'data_retention_days',
        ]


class UserProfileForm(forms.ModelForm):
    """
    Simple user profile form for basic information.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
