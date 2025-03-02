from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable, Coroutine, Union


class AudioStreamInterface(ABC):
    """Interface for audio stream management."""
    
    @abstractmethod
    def read(self) -> bytes:
        """Read audio data from the stream.
        
        Returns:
            bytes: The audio data read from the stream.
        """
        pass
    
    @abstractmethod
    def get_stream(self):
        """Get the underlying audio stream.
        
        Returns:
            The audio stream object.
        """
        pass
    
    @abstractmethod
    def is_stream_closed(self) -> bool:
        """Check if the audio stream is closed.
        
        Returns:
            bool: True if the stream is closed, False otherwise.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources used by the audio stream."""
        pass
    
    @abstractmethod
    def initialize_stream(self, rate: int, channels: int, audio_format: int, frames_per_buffer: int) -> None:
        """Initialize the audio stream with the given parameters.
        
        Args:
            rate: Sample rate of the audio stream.
            channels: Number of audio channels.
            audio_format: Format of the audio stream.
            frames_per_buffer: Number of audio frames per buffer.
        """
        pass
    
    @abstractmethod
    def update_rolling_buffer(self, data: bytes) -> None:
        """Update the rolling buffer with new audio data.
        
        Args:
            data: The audio data to add to the rolling buffer.
        """
        pass
    
    @abstractmethod
    def get_rolling_buffer(self) -> bytes:
        """Get the current rolling buffer audio data.
        
        Returns:
            bytes: The current audio data in the rolling buffer.
        """
        pass


class TranscriberInterface(ABC):
    """Interface for audio transcription services."""
    
    @abstractmethod
    def transcribe_audio(self, audio_file_path: str, language: str = "en") -> str:
        """Transcribe an audio file.
        
        Args:
            audio_file_path: Path to the audio file to transcribe.
            language: Language code (default: 'en' for English).
            
        Returns:
            str: The transcribed text or empty string if error.
        """
        pass
    
    @abstractmethod
    def transcribe_file(self, audio_file_path: str, language: str = "en") -> Dict[str, Any]:
        """Transcribe an audio file with detailed response.
        
        Args:
            audio_file_path: Path to the audio file to transcribe.
            language: Language code (default: 'en' for English).
            
        Returns:
            Dict[str, Any]: Dictionary containing transcription results or error information.
        """
        pass
    
    @abstractmethod
    def transcribe_bytes(self, audio_bytes: bytes, language: str = "en") -> Dict[str, Any]:
        """Transcribe audio from bytes.
        
        Args:
            audio_bytes: Audio data as bytes.
            language: Language code (default: 'en' for English).
            
        Returns:
            Dict[str, Any]: Dictionary containing transcription results or error information.
        """
        pass


class WakeWordDetectorInterface(ABC):
    """Interface for wake word detection."""
    
    @abstractmethod
    def run(self) -> None:
        """Start the wake word detection in a non-blocking way."""
        pass
    
    @abstractmethod
    def run_blocking(self) -> None:
        """Start the wake word detection and block until detection occurs."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources used by the wake word detector."""
        pass


class ActionManagerInterface(ABC):
    """Interface for managing actions triggered by voice commands."""
    
    @abstractmethod
    def register_action(self, action_function: Callable) -> None:
        """Register a new action function.
        
        Args:
            action_function: The function to register as an action.
        """
        pass
    
    @abstractmethod
    async def execute_actions(self) -> None:
        """Execute all registered action functions."""
        pass


class AudioRecorderInterface(ABC):
    """Interface for audio recording."""
    
    @abstractmethod
    def perform_recording(self) -> Optional[str]:
        """Start the recording process.
        
        Returns:
            str or None: The path to the recorded audio file, or None if no file was recorded.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources used by the audio recorder."""
        pass


class VoiceProcessingManagerInterface(ABC):
    """Interface for the voice processing manager."""
    
    @abstractmethod
    def run(self, transcription: bool = True) -> Optional[str]:
        """Process a voice command.
        
        Args:
            transcription: If True, perform transcription on the recording.
            
        Returns:
            str or None: The transcribed text or None if no valid recording was made.
        """
        pass
    
    @abstractmethod
    def setup(self) -> None:
        """Initialize the components of the voice processing manager."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources used by the voice processing manager."""
        pass
    
    @classmethod
    @abstractmethod
    def create_default_instance(cls, **kwargs) -> 'VoiceProcessingManagerInterface':
        """Create a default instance of the voice processing manager.
        
        Returns:
            VoiceProcessingManagerInterface: A new instance with default settings.
        """
        pass 