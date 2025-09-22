from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .services import AIOrchestrationService, StandupParsingService
import tempfile
import os


class AIProcessingView(APIView):
    """
    Main API View for AI processing operations including standup processing and speech-to-text.
    Consolidates all AI processing functionality into a single endpoint.
    """
    permission_classes = [AllowAny]  # Allow processing without authentication for frontend forms
    
    def post(self, request, *args, **kwargs):
        """
        Process AI requests - supports both text and audio inputs.
        """
        # Extract request data
        audio_duration = request.data.get('audio_duration')
        text_update = request.data.get('text_update')
        audio_file = request.FILES.get('audio')
        context = request.data.get('context', {})
        
        # Determine processing type
        if audio_file:
            return self._process_audio_file(audio_file)
        elif audio_duration or text_update:
            return self._process_standup(audio_duration, text_update, context, request.user)
        else:
            return Response(
                {"error": "Either 'audio_file', 'audio_duration', or 'text_update' must be provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _process_standup(self, audio_duration, text_update, context, user):
        """Process standup updates."""
        try:
            service = AIOrchestrationService()
            result = service.process_standup(
                audio_duration=audio_duration,
                text_update=text_update,
                context=context,
                user=user if user and user.is_authenticated else None
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Standup processing failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _process_audio_file(self, audio_file):
        """Process uploaded audio file for transcription."""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                for chunk in audio_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            # Transcribe the audio file
            from .services import SpeechToTextService
            service = SpeechToTextService()
            transcription = service.transcribe_audio(temp_file_path)
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            return Response({"transcription": transcription}, status=status.HTTP_200_OK)
        except Exception as e:
            # Clean up temporary file if it exists
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            return Response(
                {"error": f"Audio processing failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StandupParsingView(APIView):
    """
    API View for parsing standup transcriptions into structured data.
    Takes raw transcription text and segments it into yesterday, today, and blockers.
    """
    permission_classes = [AllowAny]  # Allow parsing without authentication
    
    def post(self, request, *args, **kwargs):
        """
        Parse standup transcription into structured fields.
        
        Expected input: {"transcription": "raw transcription text"}
        Returns: {"yesterday": "...", "today": "...", "blockers": "..."}
        """
        transcription = request.data.get('transcription')
        
        if not transcription:
            return Response(
                {"error": "Transcription text is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Use the parsing service to structure the transcription
            parsing_service = StandupParsingService()
            parsed_data = parsing_service.parse_standup_transcription(transcription)
            
            return Response(parsed_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # If parsing fails, return transcription as today's plan
            fallback_data = {
                "yesterday": "",
                "today": transcription.strip(),
                "blockers": ""
            }
            return Response(fallback_data, status=status.HTTP_200_OK)
