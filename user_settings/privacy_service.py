"""
Privacy enforcement service for managing user consent and data processing controls.
"""
from django.contrib.auth.models import User
from .models import UserSettings


class PrivacyEnforcementService:
    """Service for checking and enforcing privacy settings across the application."""
    
    @staticmethod
    def get_user_privacy_status(user: User) -> dict:
        """Get comprehensive privacy status for a user."""
        try:
            settings, created = UserSettings.objects.get_or_create(user=user)
            
            return {
                'sentiment_analysis': {
                    'enabled': settings.allow_sentiment_analysis,
                    'description': 'AI analyses mood and sentiment in standup updates',
                    'data_processed': 'Text content, sentiment scores, confidence levels'
                },
                'ai_analysis': {
                    'enabled': settings.allow_ai_analysis,
                    'description': 'AI generates insights and summaries from work data',
                    'data_processed': 'Standup text, work patterns, productivity metrics'
                },
                'team_analytics': {
                    'enabled': settings.allow_team_analytics,
                    'description': 'Include your data in team-wide analytics and insights',
                    'data_processed': 'Aggregated metrics, productivity scores, team comparisons'
                },
                'voice_processing': {
                    'enabled': settings.allow_voice_processing,
                    'description': 'Voice input processing and speech-to-text conversion',
                    'data_processed': 'Audio recordings, transcriptions, voice patterns'
                },
                'external_integrations': {
                    'enabled': settings.allow_external_integrations,
                    'description': 'Connect with GitHub, Jira, and other external tools',
                    'data_processed': 'API keys, work items, external account data'
                },
                'anonymous_mode': {
                    'enabled': settings.anonymous_mode,
                    'description': 'Hide identifying information in team analytics',
                    'data_processed': 'Anonymised user IDs instead of names'
                },
                'data_retention': {
                    'days': settings.data_retention_days,
                    'description': f'Automatically delete personal data after {settings.data_retention_days} days',
                    'data_processed': 'All personal standup data, AI analysis results'
                }
            }
        except Exception as e:
            print(f"Error getting privacy status: {e}")
            return {}
    
    @staticmethod
    def check_processing_consent(user: User, operation_type: str) -> tuple[bool, str]:
        """Check if user has consented to a specific type of data processing."""
        try:
            settings, created = UserSettings.objects.get_or_create(user=user)
            
            consent_checks = {
                'sentiment_analysis': (settings.allow_sentiment_analysis, 'sentiment analysis'),
                'ai_analysis': (settings.allow_ai_analysis, 'AI analysis'),
                'team_analytics': (settings.allow_team_analytics, 'team analytics'),
                'voice_processing': (settings.allow_voice_processing, 'voice processing'),
                'external_integrations': (settings.allow_external_integrations, 'external integrations')
            }
            
            if operation_type in consent_checks:
                consent_given, operation_name = consent_checks[operation_type]
                if consent_given:
                    return True, f"{operation_name} consent granted"
                else:
                    return False, f"{operation_name} disabled in privacy settings"
            
            return False, f"Unknown operation type: {operation_type}"
            
        except Exception as e:
            print(f"Error checking processing consent: {e}")
            return False, f"Error checking consent: {e}"
    
    @staticmethod
    def get_processing_summary(user: User) -> dict:
        """Get summary of what data processing is currently enabled for user."""
        try:
            settings, created = UserSettings.objects.get_or_create(user=user)
            
            enabled_features = []
            disabled_features = []
            
            features = [
                ('sentiment_analysis', 'Sentiment Analysis', settings.allow_sentiment_analysis),
                ('ai_analysis', 'AI Analysis & Summaries', settings.allow_ai_analysis),
                ('team_analytics', 'Team Analytics Inclusion', settings.allow_team_analytics),
                ('voice_processing', 'Voice Input Processing', settings.allow_voice_processing),
                ('external_integrations', 'External Tool Integrations', settings.allow_external_integrations),
            ]
            
            for feature_key, feature_name, is_enabled in features:
                if is_enabled:
                    enabled_features.append(feature_name)
                else:
                    disabled_features.append(feature_name)
            
            privacy_level = "High" if len(disabled_features) >= 3 else "Medium" if len(disabled_features) >= 1 else "Standard"
            
            return {
                'privacy_level': privacy_level,
                'enabled_features': enabled_features,
                'disabled_features': disabled_features,
                'anonymous_mode': settings.anonymous_mode,
                'data_retention_days': settings.data_retention_days,
                'total_features': len(features),
                'enabled_count': len(enabled_features),
                'disabled_count': len(disabled_features)
            }
            
        except Exception as e:
            print(f"Error getting processing summary: {e}")
            return {
                'privacy_level': 'Unknown',
                'enabled_features': [],
                'disabled_features': [],
                'error': str(e)
            }
    
    @staticmethod
    def apply_data_retention_policy(user: User) -> dict:
        """Apply data retention policy for a user (simulate cleanup)."""
        try:
            settings, created = UserSettings.objects.get_or_create(user=user)
            retention_days = settings.data_retention_days
            
            # In a real implementation, this would:
            # 1. Find all standup sessions older than retention_days
            # 2. Delete or anonymise the data
            # 3. Clear AI analysis results
            # 4. Remove external integration cache
            
            return {
                'status': 'success',
                'retention_days': retention_days,
                'message': f'Data retention policy applied - data older than {retention_days} days would be removed',
                'simulated': True  # This is just a demo
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error applying data retention policy: {e}'
            }
    
    # Add compatibility methods for dashboard service integration
    @staticmethod
    def has_consent(user, consent_type):
        """Check if user has given consent for a specific type of processing."""
        try:
            settings, created = UserSettings.objects.get_or_create(user=user)
        except Exception:
            return False
        
        # Map consent types to UserSettings fields
        consent_mapping = {
            'sentiment_analysis': settings.allow_sentiment_analysis,
            'ai_analysis': settings.allow_ai_analysis,
            'team_analytics': settings.allow_team_analytics,
            'voice_processing': settings.allow_voice_processing,
            'external_integrations': settings.allow_external_integrations,
        }
        
        return consent_mapping.get(consent_type, False)
    
    @staticmethod
    def check_processing_consent(user, processing_type):
        """Check if user has consented to specific processing."""
        try:
            settings, created = UserSettings.objects.get_or_create(user=user)
        except Exception:
            return False
        
        # Simplified mapping for MVP
        processing_mapping = {
            'ai_analysis': settings.allow_ai_analysis,
            'sentiment_analysis': settings.allow_sentiment_analysis,
            'voice_recording': settings.allow_voice_processing,
            'team_analytics': settings.allow_team_analytics,
            'external_sync': settings.allow_external_integrations,
        }
        
        return processing_mapping.get(processing_type, False)
    
    @staticmethod
    def get_consent_summary(user):
        """Get a simple summary of user consent settings."""
        try:
            settings, created = UserSettings.objects.get_or_create(user=user)
            return {
                'sentiment_analysis': settings.allow_sentiment_analysis,
                'ai_analysis': settings.allow_ai_analysis,
                'team_analytics': settings.allow_team_analytics,
                'voice_processing': settings.allow_voice_processing,
                'external_integrations': settings.allow_external_integrations,
            }
        except Exception:
            return {
                'sentiment_analysis': False,
                'ai_analysis': False,
                'team_analytics': False,
                'voice_processing': False,
                'external_integrations': False,
            }