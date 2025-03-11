import logging
import os
import threading
import time
import signal
from typing import Optional, Dict, Any, Union

import pyaudio

from VoiceProcessingToolkit.transcription.elevenlabs import ElevenLabsTranscriber
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager
from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
from VoiceProcessingToolkit.audio.AudioManager import AudioManager
from VoiceProcessingToolkit.config import get_config, Config
from VoiceProcessingToolkit.interfaces import VoiceProcessingManagerBase

logger = logging.getLogger(__name__)

# Thread manager for local use (not global)
class ThreadManager:
    """Thread manager for tracking and cleaning up threads."""
    
    def __init__(self):
        self.threads = []
        self.shutdown_requested = threading.Event()
    
    def add_thread(self, thread):
        """Add a thread to the manager."""
        self.threads.append(thread)
    
    def request_shutdown(self):
        """Request all threads to shut down."""
        self.shutdown_requested.set()
    
    def join_all(self, timeout=None):
        """Wait for all threads to complete."""
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout)
        self.threads = [t for t in self.threads if t.is_alive()]

class VoiceProcessingManager(VoiceProcessingManagerBase):
    """
    Manages the voice processing pipeline, including optional wake word detection, voice recording, and transcription.
    This class integrates different components using a central configuration and dependency injection.
    
    Use the create_with_config factory method for the most streamlined initialization.
    """
    
    def __init__(self, config: Config, thread_manager: Optional[ThreadManager] = None, components: Optional[Dict[str, Any]] = None):
        """
        Initialize with a config object and optional component overrides.
        
        Args:
            config: Configuration object containing all settings
            thread_manager: Optional thread manager for tracking created threads
            components: Optional dictionary of pre-configured components to use
                Supported keys: 'transcriber', 'action_manager', 'audio_manager', 'wake_word_detector', 'voice_recorder'
        """
        self.config = config
        self.thread_manager = thread_manager or ThreadManager()
        self.transcriber = None
        self.action_manager = None
        self.audio_manager = None
        self.wake_word_detector = None
        self.voice_recorder = None
        
        # Set defaults for operation mode
        self.use_wake_word = config.use_wake_word
        self.play_notification_sound = config.play_notification_sound
        self.save_wake_word_recordings = config.save_wake_word_recordings
        
        # Set up components, using provided ones or creating from config
        self._setup_components(components or {})
        logger.info("VoiceProcessingManager initialized")
        
    def _setup_components(self, components: Dict[str, Any]) -> None:
        """
        Set up all required components, using provided ones or creating defaults.
        
        Args:
            components: Dictionary of pre-configured components
        """
        # Create audio manager if not provided
        self.audio_manager = components.get('audio_manager') or AudioManager(
            rate=self.config.audio_rate,
            channels=self.config.audio_channels, 
            audio_format=pyaudio.paInt16,
            frames_per_buffer=self.config.frames_per_buffer,
            buffer_duration=self.config.buffer_length
        )
        
        # Create action manager if not provided
        self.action_manager = components.get('action_manager') or ActionManager()
        
        # Create wake word detector if not provided
        self.wake_word_detector = components.get('wake_word_detector') or WakeWordDetector(
            access_key=self.config.wake_word_access_key,
            wake_word=self.config.wake_word,
            sensitivity=self.config.wake_word_sensitivity,
            action_manager=self.action_manager,
            audio_stream_manager=self.audio_manager,  # Using AudioManager instead of AudioStream
            play_notification_sound=self.play_notification_sound,
            save_audio_directory=self.config.wake_word_output if self.save_wake_word_recordings else None
        )
        
        # Create voice recorder if not provided
        self.voice_recorder = components.get('voice_recorder') or AudioRecorder(
            output_dir=self.config.output_dir,
            rate=self.config.audio_rate,
            channels=self.config.audio_channels,
            frames_per_buffer=self.config.frames_per_buffer,
            voice_threshold=self.config.voice_threshold,
            inactivity_limit=self.config.inactivity_limit,
            min_recording_length=self.config.min_recording_length,
            buffer_length=self.config.buffer_length
        )
        
        # Create transcriber if not provided
        self.transcriber = components.get('transcriber') or ElevenLabsTranscriber(
            api_key=self.config.transcriber_api_key
        )
    
    @classmethod
    def create_with_config(cls, config_path: Optional[str] = None, **kwargs) -> 'VoiceProcessingManager':
        """
        Create a VoiceProcessingManager using a configuration file or defaults with optional overrides.
        
        Args:
            config_path: Path to configuration file (optional)
            **kwargs: Override specific configuration values
            
        Returns:
            VoiceProcessingManager: Configured instance
        """
        # Load config from file or use default
        config = get_config(config_path)
        
        # Override config values with any provided in kwargs
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Create the manager instance
        instance = cls(config)
        
        return instance
        
    def run(self, transcription: bool = True) -> Optional[str]:
        """
        Run the voice processing pipeline.
        
        Args:
            transcription: Whether to transcribe the recorded audio
            
        Returns:
            str or None: Transcription text if transcription is True and successful, None otherwise
        """
        logger.info("Starting voice processing pipeline")
        
        if self.use_wake_word:
            # Step 1: Wait for wake word
            logger.info(f"Listening for wake word: '{self.config.wake_word}'")
            wake_word_detected = self.wake_word_detector.run_blocking()
            
            if not wake_word_detected:
                logger.info("Wake word detection interrupted")
                return None
                
            logger.info("Wake word detected, proceeding to recording")
        
        # Step 2: Record voice
        logger.info("Starting audio recording")
        audio_file = self.voice_recorder.perform_recording()
        
        if not audio_file:
            logger.warning("No audio file was recorded")
            return None
            
        logger.info(f"Audio recorded to: {audio_file}")
        
        # Step 3: Transcribe audio if requested
        if transcription:
            logger.info("Transcribing audio")
            text = self.transcriber.transcribe_audio(audio_file)
            logger.info(f"Transcription result: {text}")
            return text
        
        return None
    
    def cleanup(self) -> None:
        """
        Clean up all resources used by the manager and its components.
        """
        logger.info("Cleaning up VoiceProcessingManager resources")
        
        # Request all threads to shut down
        self.thread_manager.request_shutdown()
        
        # Clean up components
        if self.wake_word_detector:
            self.wake_word_detector.cleanup()
            
        if self.voice_recorder:
            self.voice_recorder.cleanup()
            
        if self.audio_manager:
            self.audio_manager.cleanup()
            
        # Wait for threads to complete
        self.thread_manager.join_all(timeout=2.0)
        
        logger.info("VoiceProcessingManager cleanup complete")
    
    def __enter__(self):
        """Support for context manager pattern."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up resources when exiting context."""
        self.cleanup()
    
    def __del__(self):
        """Ensure cleanup when object is garbage collected."""
        self.cleanup()
