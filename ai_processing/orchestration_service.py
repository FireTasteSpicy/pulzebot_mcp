"""
Main AI orchestration service that coordinates all AI processing tasks.
"""
from .speech_service import SpeechToTextService
from .sentiment_service import SentimentAnalysisService
from .summary_service import SummaryGenerationService


class AIOrchestrationService:
    """Orchestrates the AI services for processing stand-up updates."""

    def __init__(self):
        """Initialise the orchestration service."""
        self.stt_service = SpeechToTextService()
        self.sentiment_service = SentimentAnalysisService()
        self.summary_service = SummaryGenerationService()

    def _check_user_privacy_settings(self, user, operation_type):
        """
        Check if user has consented to the specific AI operation.
        """
        try:
            from user_settings.models import UserSettings
            settings, created = UserSettings.objects.get_or_create(user=user)
            
            # Map operation types to privacy settings
            privacy_checks = {
                'sentiment_analysis': settings.allow_sentiment_analysis,
                'ai_analysis': settings.allow_ai_analysis,
                'voice_processing': settings.allow_voice_processing,
                'team_analytics': settings.allow_team_analytics,
                'external_integrations': settings.allow_external_integrations
            }
            
            return privacy_checks.get(operation_type, False)
        except Exception as e:
            print(f"Error checking privacy settings: {e}")
            # Default to False for privacy protection if there's an error
            return False

    def _anonymise_user_data(self, context, user):
        """
        Anonymise user data if anonymous mode is enabled.
        """
        try:
            from user_settings.models import UserSettings
            settings = UserSettings.objects.get(user=user)
            
            if settings.anonymous_mode:
                # Replace user info with anonymous data
                if 'user_info' in context:
                    context['user_info'] = {
                        'username': f"Anonymous_User_{user.id % 1000}",
                        'full_name': "Anonymous User",
                        'first_name': "Anonymous"
                    }
        except Exception as e:
            print(f"Error during anonymization: {e}")
        
        return context

    def process_standup(self, audio_duration=None, text_update=None, context=None, user=None):
        """
        Process a stand-up update, either from audio or text with privacy controls.
        """
        if not audio_duration and not text_update:
            return None

        # Privacy check - get user from context if not provided
        if not user and context and 'user_info' in context:
            try:
                from django.contrib.auth.models import User
                username = context['user_info'].get('username')
                if username:
                    user = User.objects.get(username=username)
            except:
                pass

        result = {}
        transcription = text_update

        # Voice processing privacy check
        if audio_duration:
            if user and not self._check_user_privacy_settings(user, 'voice_processing'):
                return {'error': 'Voice processing not permitted - check privacy settings'}
            
            transcription = self.stt_service.record_and_transcribe(duration=audio_duration)
            result['transcription'] = transcription

        if transcription:
            # Sentiment analysis privacy check
            sentiment = None
            if user and self._check_user_privacy_settings(user, 'sentiment_analysis'):
                sentiment = self.sentiment_service.analyse_sentiment(transcription)
            elif not user:  # Allow sentiment analysis if no user context (for demo/testing)
                sentiment = self.sentiment_service.analyse_sentiment(transcription)
            
            result['sentiment'] = sentiment
            
            # Prepare context for summary generation
            summary_context = context or {}
            
            # Only add sentiment analysis if not already provided in context
            if "sentiment_data" not in summary_context:
                # Handle case where sentiment analysis returns None
                if sentiment:
                    sentiment_label = sentiment.get('label', 'Neutral')
                    sentiment_score = sentiment.get('score', 0.0)
                else:
                    sentiment_label = 'Neutral'
                    sentiment_score = 0.0
                
                summary_context["sentiment_data"] = {
                    "overall_sentiment": sentiment_label,
                    "confidence": sentiment_score,
                    "recent_updates": [{"text": transcription, "sentiment": sentiment_label, "confidence": sentiment_score}]
                }
            
            # Ensure GitHub and Jira data have defaults if not provided
            if "github_data" not in summary_context:
                summary_context["github_data"] = {"pull_requests": [], "issues": []}
                
            if "jira_data" not in summary_context:
                # Import here to avoid circular imports
                try:
                    from integrations.services import JiraService
                    mock_jira = JiraService(use_mock_data=True)
                    mock_sprint = mock_jira.get_sprint_info()
                    summary_context["jira_data"] = {
                        "issues": [], 
                        "sprint_info": {
                            "completed_story_points": mock_sprint.get('completed_story_points', 15),
                            "total_story_points": mock_sprint.get('total_story_points', 30),
                            "team_velocity": mock_sprint.get('team_velocity', 28),
                            "goal": mock_sprint.get('goal', 'Sprint goal not available')
                        }
                    }
                except ImportError:
                    # Fallback if import fails
                    summary_context["jira_data"] = {"issues": [], "sprint_info": {"completed_story_points": 15, "total_story_points": 30, "team_velocity": 28, "goal": "Sprint goal not available"}}
            
            # AI Analysis privacy check for summary generation
            summary = None
            if user and self._check_user_privacy_settings(user, 'ai_analysis'):
                # Anonymise context if needed
                summary_context = self._anonymise_user_data(summary_context, user)
                
                try:
                    summary = self.summary_service.generate_summary(summary_context)
                except Exception as e:
                    print(f"Error generating summary: {e}")
                    summary = "Summary generation failed"
            elif not user:  # Allow AI analysis if no user context (for demo/testing)
                try:
                    summary = self.summary_service.generate_summary(summary_context)
                except Exception as e:
                    print(f"Error generating summary: {e}")
                    summary = "Summary generation failed"
            else:
                summary = "AI analysis disabled in privacy settings"
            
            result['summary'] = summary

        return result