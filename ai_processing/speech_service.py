"""
Speech-to-text services for audio processing.
"""
import os
import tempfile
import whisper
from .utils import AudioPreprocessor

try:
    import pyaudio  # May fail or access ALSA on some environments; defer usage
except Exception:
    pyaudio = None
import wave


class AudioRecorder:
    """Service for recording audio from microphone."""

    def __init__(self, chunk=1024, channels=1, rate=44100):
        """Initialise the audio recorder."""
        self.chunk = chunk
        self.format = 8  # pyaudio.paInt16
        self.channels = channels
        self.rate = rate
        # Lazy/defensive initialization to avoid ALSA errors on systems without audio devices (e.g., WSL/servers)
        if pyaudio is None:
            raise RuntimeError("PyAudio is unavailable in this environment")
        try:
            self.p = pyaudio.PyAudio()
        except Exception as e:
            # Propagate a clear error without spewing ALSA logs
            raise RuntimeError(f"Audio device unavailable: {e}")

    def record_audio(self, duration, output_filename=None):
        """
        Record audio from microphone and return the file path.
        """
        stream = self.p.open(format=self.format,
                             channels=self.channels,
                             rate=self.rate,
                             input=True,
                             frames_per_buffer=self.chunk)
        
        frames = []
        for _ in range(0, int(self.rate / self.chunk * duration)):
            data = stream.read(self.chunk)
            frames.append(data)
            
        stream.stop_stream()
        stream.close()

        if output_filename is None:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            output_filename = temp_file.name
        
        wf = wave.open(output_filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return output_filename


class WhisperTranscriber:
    """Service for transcribing audio using Whisper."""

    def __init__(self, model_name="base"):
        """Initialise the transcriber."""
        self.model = whisper.load_model(model_name)

    def transcribe_audio(self, audio_file_path):
        """
        Transcribe audio file using local Whisper model.
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found at {audio_file_path}")
            
        try:
            result = self.model.transcribe(audio_file_path, language="en")
            return {'text': result["text"].strip()}
        except Exception as e:
            print(f"Whisper transcription error: {e}")
            raise Exception(f"Transcription failed: {e}")


class SpeechToTextService:
    """Orchestrates audio recording and transcription."""

    def __init__(self):
        """Initialise the service."""
        # Do not touch audio hardware at import/initialization time
        self.recorder = None
        self.transcriber = WhisperTranscriber()
        self.preprocessor = AudioPreprocessor()
        self.model = getattr(self.transcriber, 'model', None) 

    def transcribe_audio(self, file_path):
        """
        Transcribe audio from file path.
        """
        processed_audio_file = None
        try:
            if not os.path.exists(file_path):
                return None
            processed_audio_file = self.preprocessor.process(file_path)
            transcription = self.transcriber.transcribe_audio(processed_audio_file)
            return transcription
        except Exception as e:
            print(f"Transcription failed: {e}")
            return "Transcription failed. Please try again."
        finally:
            if processed_audio_file and processed_audio_file != file_path and os.path.exists(processed_audio_file):
                os.unlink(processed_audio_file)

    def record_and_transcribe(self, duration, output_filename=None):
        """
        Record and transcribe audio.
        """
        raw_audio_file = None
        processed_audio_file = None
        try:
            # Lazy-create the recorder only when needed; gracefully degrade if unavailable
            if self.recorder is None:
                try:
                    self.recorder = AudioRecorder()
                except Exception as e:
                    return f"Recording not available in this environment: {e}"
            raw_audio_file = self.recorder.record_audio(duration=duration, output_filename=output_filename)
            processed_audio_file = self.preprocessor.process(raw_audio_file)
            transcription = self.transcriber.transcribe_audio(processed_audio_file)
            return transcription
        except Exception as e:
            print(f"Transcription failed: {e}")
            return "Transcription failed. Please try again."
        finally:
            if raw_audio_file and output_filename is None and os.path.exists(raw_audio_file):
                os.unlink(raw_audio_file)
            if processed_audio_file and os.path.exists(processed_audio_file):
                os.unlink(processed_audio_file)