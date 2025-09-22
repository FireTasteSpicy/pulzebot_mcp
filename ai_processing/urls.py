from django.urls import path
from .views import AIProcessingView, StandupParsingView

app_name = 'ai_processing'

# Consolidated AI processing endpoints
urlpatterns = [
    # Main processing endpoint - handles all AI processing operations
    path('process/', AIProcessingView.as_view(), name='process_standup'),
    
    # Standup parsing endpoint - segments transcription into structured fields
    path('standup/parse/', StandupParsingView.as_view(), name='standup_parse'),
    
    # Aliases for backward compatibility
    path('standup/process/', AIProcessingView.as_view(), name='standup_process'),
    path('speech/transcribe/', AIProcessingView.as_view(), name='speech_to_text'),
]
