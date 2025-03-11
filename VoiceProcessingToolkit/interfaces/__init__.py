"""
Interfaces for VoiceProcessingToolkit components.

This module provides interface definitions for the various components
of the VoiceProcessingToolkit, enabling better code organization, type checking,
and extensibility through well-defined abstractions.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict


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