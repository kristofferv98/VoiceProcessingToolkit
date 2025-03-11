"""
Interfaces and base classes for VoiceProcessingToolkit components.

This module provides interface definitions and base classes for the various components
of the VoiceProcessingToolkit, enabling better code organization, type checking,
and extensibility through well-defined abstractions.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict, List, Callable


class TranscriberInterface(ABC):
    """Interface for audio transcription components (keeping as interface since we have multiple implementations)."""
    
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


class AudioRecorderBase:
    """Base class for audio recording components."""
    
    def perform_recording(self) -> Optional[str]:
        """
        Start recording audio until certain conditions are met.
        
        Returns:
            str or None: Path to the recorded audio file if successful, None otherwise.
        """
        raise NotImplementedError("Subclasses must implement perform_recording")
    
    def cleanup(self) -> None:
        """Release all resources used by the recorder."""
        pass


class WakeWordDetectorBase:
    """Base class for wake word detection components."""
    
    def run_blocking(self) -> bool:
        """
        Run wake word detection in a blocking manner.
        
        Returns:
            bool: True if wake word was detected, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement run_blocking")
    
    def run_async(self) -> None:
        """Start wake word detection asynchronously."""
        raise NotImplementedError("Subclasses must implement run_async")
    
    def cleanup(self) -> None:
        """Release all resources used by the detector."""
        pass


class ActionManagerBase:
    """Base class for action management components."""
    
    def on_wake_word_detected(self) -> None:
        """
        Handle the wake word detection event.
        This method is called when a wake word is detected.
        """
        raise NotImplementedError("Subclasses must implement on_wake_word_detected")
    
    def register_action(self, action_name: str, action_func: Callable) -> None:
        """
        Register an action to be executed on wake word detection.
        
        Args:
            action_name: Name of the action to register.
            action_func: Function to execute when the action is triggered.
        """
        raise NotImplementedError("Subclasses must implement register_action")


class VoiceProcessingManagerBase:
    """Base class for voice processing manager components."""
    
    def run(self, transcription: bool = True) -> Optional[str]:
        """
        Run the voice processing pipeline.
        
        Args:
            transcription: Flag to indicate whether to perform transcription.
            
        Returns:
            str or None: The transcription result, if available.
        """
        raise NotImplementedError("Subclasses must implement run")
    
    def cleanup(self) -> None:
        """Release all resources used by the manager."""
        pass
    
    def setup(self) -> None:
        """Initialize components needed for voice processing."""
        pass


# Keep backward compatibility
AudioRecorderInterface = AudioRecorderBase
WakeWordDetectorInterface = WakeWordDetectorBase
AudioStreamInterface = object  # No longer needed with the consolidated AudioManager
ActionManagerInterface = ActionManagerBase
VoiceProcessingManagerInterface = VoiceProcessingManagerBase 