"""
AI Processing Services - Main module importing from specialised service files.

This module provides a clean interface to all AI processing capabilities
by importing from specialised service modules.
"""

# Import all services from their specialised modules
from .sentiment_service import SentimentAnalysisService
from .summary_service import SummaryGenerationService
from .speech_service import SpeechToTextService, AudioRecorder, WhisperTranscriber
from .orchestration_service import AIOrchestrationService
from .parsing_service import StandupParsingService

# Export all services for backward compatibility (Before module restructuring)
__all__ = [
    'SentimentAnalysisService',
    'SummaryGenerationService', 
    'SpeechToTextService',
    'AudioRecorder',
    'WhisperTranscriber',
    'AIOrchestrationService',
    'StandupParsingService'
]


