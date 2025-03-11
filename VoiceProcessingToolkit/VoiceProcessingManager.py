import logging
import os
import threading
import time
import signal
from typing import Optional, Dict, Any, Union

import pyaudio

from VoiceProcessingToolkit.transcription.elevenlabs import ElevenLabsTranscriber
from VoiceProcessingToolkit.wake_word_detector.AudioStreamManager import AudioStream
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager
from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
from VoiceProcessingToolkit.shared_resources import thread_manager
from VoiceProcessingToolkit.config import get_config, Config
from VoiceProcessingToolkit.interfaces import VoiceProcessingManagerInterface

logger = logging.getLogger(__name__)

class VoiceProcessingManager(VoiceProcessingManagerInterface):
    """
    Manages the voice processing pipeline, including optional wake word detection, voice recording, and transcription.
    This class integrates different components using a central configuration and dependency injection.
    
    Use the create_with_config factory method for the most streamlined initialization.
    """
    
    def __init__(self, config: Config, components: Optional[Dict[str, Any]] = None):
        """
        Initialize with a config object and optional component overrides.
        
        Args:
            config: Configuration object containing all settings
            components: Optional dictionary of pre-configured components to use
                Supported keys: 'transcriber', 'action_manager', 'audio_stream', 'wake_word_detector', 'voice_recorder'
        """
        self.config = config
        self.transcriber = None
        self.action_manager = None
        self.audio_stream_manager = None
        self.wake_word_detector = None
        self.voice_recorder = None
        
        # Save configuration values as instance variables for compatibility
        self.wake_word = config.wake_word.wake_word
        self.sensitivity = config.wake_word.sensitivity
        self.output_directory = config.paths.output_dir
        self.wake_word_output = os.path.join(config.paths.output_dir, "wake_word_dataset")
        self.audio_format = pyaudio.paInt16
        self.channels = config.audio.channels
        self.rate = config.audio.rate
        self.frames_per_buffer = config.audio.frames_per_buffer
        self.voice_threshold = config.audio.voice_threshold
        self.silence_limit = 2.0
        self.inactivity_limit = config.audio.inactivity_limit
        self.min_recording_length = config.audio.min_recording_length
        self.buffer_length = config.audio.buffer_length
        self.use_wake_word = True  # Default value, can be overridden in run method
        self.save_wake_word_recordings = False
        self.play_notification_sound = True
        
        # Set up components, using provided ones or creating from config
        self._setup_components(components or {})
        
    def _setup_components(self, components: Dict[str, Any]) -> None:
        """
        Set up all required components, using provided ones or creating defaults.
        
        Args:
            components: Dictionary of pre-configured components
        """
        # Create audio stream manager if not provided
        self.audio_stream_manager = components.get('audio_stream') or AudioStream(
            rate=self.rate,
            channels=self.channels, 
            _audio_format=self.audio_format,
            frames_per_buffer=self.frames_per_buffer
        )
        
        # Create action manager if not provided
        self.action_manager = components.get('action_manager') or ActionManager()
        
        # Create wake word detector if not provided
        self.wake_word_detector = components.get('wake_word_detector') or WakeWordDetector(
            access_key=self.config.wake_word.access_key,
            wake_word=self.wake_word,
            sensitivity=self.sensitivity,
            action_manager=self.action_manager,
            audio_stream_manager=self.audio_stream_manager,
            play_notification_sound=self.play_notification_sound,
            save_audio_directory=self.wake_word_output if self.save_wake_word_recordings else None
        )
        
        # Create voice recorder if not provided
        self.voice_recorder = components.get('voice_recorder') or AudioRecorder(
            output_dir=self.output_directory,
            voice_threshold=self.voice_threshold,
            inactivity_limit=self.inactivity_limit,
            min_recording_length=self.min_recording_length,
            buffer_length=self.buffer_length
        )
        
        # Create transcriber if not provided
        self.transcriber = components.get('transcriber') or ElevenLabsTranscriber(
            api_key=self.config.transcriber.api_key
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
        if 'wake_word' in kwargs:
            config.wake_word.wake_word = kwargs['wake_word']
        if 'sensitivity' in kwargs:
            config.wake_word.sensitivity = kwargs['sensitivity']
        if 'use_wake_word' in kwargs:
            # This will be used when instantiating but isn't part of the config object
            use_wake_word = kwargs['use_wake_word']
        else:
            use_wake_word = True
        if 'play_notification_sound' in kwargs:
            play_notification_sound = kwargs['play_notification_sound']
        else:
            play_notification_sound = True
        if 'save_wake_word_recordings' in kwargs:
            save_wake_word_recordings = kwargs['save_wake_word_recordings'] 
        else:
            save_wake_word_recordings = False
            
        # Create the manager instance
        instance = cls(config)
        
        # Set non-config properties that influence behavior
        instance.use_wake_word = use_wake_word
        instance.play_notification_sound = play_notification_sound
        instance.save_wake_word_recordings = save_wake_word_recordings
        
        return instance
        
    @classmethod
    def create_default_instance(cls, **kwargs) -> 'VoiceProcessingManager':
        """
        Create a default instance with optional parameter overrides.
        
        This is maintained for backward compatibility. New code should use create_with_config.
        
        Args:
            **kwargs: Override parameters
                
        Returns:
            VoiceProcessingManager: Configured instance
        """
        logger.info("Creating default VoiceProcessingManager instance")
        return cls.create_with_config(None, **kwargs)

    def run(self, transcription=True):
        """
        Run the voice processing pipeline.

        Args:
            transcription (bool, optional): Flag to indicate whether to perform transcription. Defaults to True.

        Returns:
            str or None: The transcription result, if available.
        """
        try:
            self.setup()
            
            # Register a cleanup handler for SIGINT
            signal_handler = signal.getsignal(signal.SIGINT)
            def cleanup_handler(sig, frame):
                logger.info("Received interrupt signal, cleaning up...")
                self.cleanup()
                # Call the original handler, if it exists
                if signal_handler and callable(signal_handler):
                    signal_handler(sig, frame)
            signal.signal(signal.SIGINT, cleanup_handler)
            
            if self.use_wake_word:
                logger.info(f"Running with wake word detection. Wake word: {self.wake_word}")
                return self._process_voice_command(transcription)
            else:
                logger.info("Running without wake word detection.")
                self.voice_recorder.perform_recording()
                
                # Wait for the recording to complete with a timeout
                if self.voice_recorder.recording_thread:
                    self.voice_recorder.recording_thread.join(timeout=60.0)
                    if self.voice_recorder.recording_thread.is_alive():
                        logger.warning("Recording thread did not complete within the timeout period. Continuing anyway.")
                
                transcription_result = None
                if transcription and self.voice_recorder.last_saved_file:
                    logger.info(f"Transcribing file: {self.voice_recorder.last_saved_file}")
                    transcription_result = self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
                    logger.info(f"Transcription result: {transcription_result}")
                
                return transcription_result

        except Exception as e:
            logger.exception("An error occurred during voice processing.", exc_info=e)
            self.cleanup()
            raise

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, performing cleanup.")
            self.cleanup()
            raise  # Re-raise the KeyboardInterrupt to propagate it to the caller


        finally:
            self.cleanup()
            logger.info("VoiceProcessingManager run method completed.")

    def _process_voice_command(self, transcription=True):
        """
        Process a voice command with wake word detection.
        
        Args:
            transcription (bool, optional): Whether to transcribe the recording. Defaults to True.
            
        Returns:
            str or None: Transcription result if available.
        """
        logger.debug("Processing voice command with wake word detection")
        
        # Initiate wake word detection and block until it completes
        self.wake_word_detector.run_blocking()
        
        if not transcription:
            return None
            
        # Once wake word is detected, start recording
        self.voice_recorder.perform_recording()
        
        # Wait for the recording to complete with a timeout
        if self.voice_recorder.recording_thread:
            self.voice_recorder.recording_thread.join(timeout=60.0)
            if self.voice_recorder.recording_thread.is_alive():
                logger.warning("Recording thread did not complete within the timeout period.")
        
        # Check if a recording was made
        if self.voice_recorder.last_saved_file:
            # Transcribe the recording
            logger.info(f"Transcribing file: {self.voice_recorder.last_saved_file}")
            transcription_result = self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
            logger.info(f"Transcription result: {transcription_result}")
            return transcription_result
        else:
            # If no recording was made or it was too short, log the information
            logger.info("Recording was not made or was too short.")
            return None
            
    def cleanup(self):
        """
        Properly clean up all resources.
        
        This method should be called before the program exits to ensure proper resource cleanup.
        """
        logger.info("Cleaning up resources...")
        
        # Clean up thread manager
        try:
            thread_manager.shutdown()
        except Exception as e:
            logger.error(f"Error during thread manager shutdown: {e}")
        
        # Clean up wake word detector if it exists
        if hasattr(self, 'wake_word_detector') and self.wake_word_detector:
            try:
                if hasattr(self.wake_word_detector, 'cleanup'):
                    self.wake_word_detector.cleanup()
            except Exception as e:
                logger.error(f"Error during wake word detector cleanup: {e}")
        
        # Clean up voice recorder if it exists
        if hasattr(self, 'voice_recorder') and self.voice_recorder:
            try:
                if hasattr(self.voice_recorder, 'cleanup'):
                    self.voice_recorder.cleanup()
            except Exception as e:
                logger.error(f"Error during voice recorder cleanup: {e}")
        
        # Clean up audio stream manager if it exists
        if hasattr(self, 'audio_stream_manager') and self.audio_stream_manager:
            try:
                if hasattr(self.audio_stream_manager, 'cleanup'):
                    self.audio_stream_manager.cleanup()
            except Exception as e:
                logger.error(f"Error during audio stream manager cleanup: {e}")
        
        logger.info("Cleanup completed.")

    def setup(self) -> None:
        """
        Initialize the components of the voice processing manager if not already done.
        """
        # Validate API keys
        picovoice_apikey = self.config.wake_word.access_key
        elevenlabs_apikey = self.config.transcriber.api_key
        
        # Check for required API keys if wake word detection is enabled
        if self.use_wake_word and not picovoice_apikey:
            logger.error("PICOVOICE_APIKEY environment variable is not set. Wake word detection will not work.")
            raise ValueError("PICOVOICE_APIKEY environment variable is required for wake word detection.")
        
        # Create wake word detector if not provided
        if self.wake_word_detector is None:
            logger.info("Creating default wake word detector")
            self.wake_word_detector = WakeWordDetector(
                access_key=picovoice_apikey,
                wake_word=self.wake_word,
                sensitivity=self.sensitivity,
                action_manager=self.action_manager,
                audio_stream_manager=self.audio_stream_manager,
                play_notification_sound=self.play_notification_sound,
                save_audio_directory=self.wake_word_output if self.save_wake_word_recordings else None,
            )
        
        # Create voice recorder if not provided
        if self.voice_recorder is None:
            logger.info("Creating default voice recorder")
            # Use the configuration for either Cobra VAD or energy-based detection
            try:
                if self.config.audio.use_cobra_vad:
                    if not picovoice_apikey:
                        logger.warning("PICOVOICE_APIKEY not set. Falling back to energy-based voice detection.")
                        self.voice_recorder = AudioRecorder(output_dir=self.output_directory)
                    else:
                        logger.info("Using Cobra VAD for voice detection")
                        self.voice_recorder = AudioRecorder(
                            output_dir=self.output_directory,
                            voice_threshold=self.config.audio.voice_threshold,
                            inactivity_limit=self.config.audio.inactivity_limit,
                            min_recording_length=self.config.audio.min_recording_length,
                            buffer_length=self.config.audio.buffer_length
                        )
                else:
                    logger.info("Using energy-based voice detection")
                    self.voice_recorder = AudioRecorder(output_dir=self.output_directory)
            except Exception as e:
                logger.warning(f"Error reading configuration: {e}. Using default energy-based voice detection.")
                self.voice_recorder = AudioRecorder(output_dir=self.output_directory)
        
        # Create transcriber if not provided
        if self.transcriber is None:
            logger.info("Creating default transcriber")
            if not elevenlabs_apikey:
                logger.error("ELEVENLABS_API_KEY environment variable is not set. Transcription will not work.")
                raise ValueError("ELEVENLABS_API_KEY environment variable is required for transcription.")
                
            self.transcriber = ElevenLabsTranscriber(
                api_key=elevenlabs_apikey
            )
