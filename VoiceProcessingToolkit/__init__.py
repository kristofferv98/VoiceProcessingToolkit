"""
VoiceProcessingToolkit: A comprehensive toolkit for voice processing tasks.

This package provides components for wake word detection, voice recording,
transcription, and more with a modular, interface-based architecture.
"""

__version__ = "2.0.0"

# Import main components for easy access
from .VoiceProcessingManager import VoiceProcessingManager
from .interfaces import (
    AudioStreamInterface,
    TranscriberInterface,
    WakeWordDetectorInterface,
    ActionManagerInterface,
    AudioRecorderInterface,
    VoiceProcessingManagerInterface
)

# Import config and shared resources
from .config import Config
from .shared_resources import thread_manager, AudioDataProvider

# Voice Detection
from .voice_detection.Voicerecorder import AudioRecorder

# Wake Word Detection
from .wake_word_detector.WakeWordDetector import WakeWordDetector
from .wake_word_detector.AudioStreamManager import AudioStream
from .wake_word_detector.ActionManager import ActionManager

# Transcription
from .transcription.elevenlabs import ElevenLabsTranscriber

__all__ = [
    # Main components
    'VoiceProcessingManager',
    
    # Interfaces
    'AudioStreamInterface',
    'TranscriberInterface',
    'WakeWordDetectorInterface',
    'ActionManagerInterface',
    'AudioRecorderInterface',
    'VoiceProcessingManagerInterface',
    
    # Configuration
    'Config',
    
    # Shared resources
    'thread_manager',
    'AudioDataProvider',
    
    # Component implementations
    'AudioRecorder',
    'WakeWordDetector',
    'AudioStream',
    'ActionManager',
    'ElevenLabsTranscriber',
]
