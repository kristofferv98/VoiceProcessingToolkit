"""
Interfaces for VoiceProcessingToolkit components.

This module provides interface definitions for the various components
of the VoiceProcessingToolkit, enabling better code organization, type checking,
and extensibility through well-defined abstractions.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, Callable


class AudioRecorderInterface(ABC):
    """Interface for audio recording components."""
    
    @abstractmethod
    def perform_recording(self) -> Optional[str]:
        """
        Start recording audio until certain conditions are met.
        
        Returns:
            str or None: Path to the recorded audio file if successful, None otherwise.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Release all resources used by the recorder."""
        pass


class TranscriberInterface(ABC):
    """Interface for audio transcription components."""
    
    @abstractmethod
    def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio from the given file path.
        
        Args:
            audio_file_path: Path to the audio file to transcribe.
            
        Returns:
            str or None: Transcribed text if successful, None otherwise.
        """
        pass


class WakeWordDetectorInterface(ABC):
    """Interface for wake word detection components."""
    
    @abstractmethod
    def run_blocking(self) -> bool:
        """
        Run wake word detection in a blocking manner.
        
        Returns:
            bool: True if wake word was detected, False otherwise.
        """
        pass
    
    @abstractmethod
    def run_async(self) -> None:
        """Start wake word detection asynchronously."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Release all resources used by the detector."""
        pass


class AudioStreamInterface(ABC):
    """Interface for audio stream management components."""
    
    @abstractmethod
    def start(self) -> None:
        """Start the audio stream."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the audio stream."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Release all resources used by the stream."""
        pass


class ActionManagerInterface(ABC):
    """Interface for action management components."""
    
    @abstractmethod
    def on_wake_word_detected(self) -> None:
        """
        Handle the wake word detection event.
        This method is called when a wake word is detected.
        """
        pass
    
    @abstractmethod
    def register_action(self, action_name: str, action_func: Callable) -> None:
        """
        Register an action to be executed on wake word detection.
        
        Args:
            action_name: Name of the action to register.
            action_func: Function to execute when the action is triggered.
        """
        pass


class VoiceProcessingManagerInterface(ABC):
    """Interface for voice processing manager components."""
    
    @abstractmethod
    def run(self, transcription: bool = True) -> Optional[str]:
        """
        Run the voice processing pipeline.
        
        Args:
            transcription: Flag to indicate whether to perform transcription.
            
        Returns:
            str or None: The transcription result, if available.
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Release all resources used by the manager."""
        pass
    
    @abstractmethod
    def setup(self) -> None:
        """Initialize components needed for voice processing."""
        pass 