import logging
import os
import threading
import time
from threading import Thread
from typing import Optional, Dict, Any, Union, Type, List

import pyaudio

from VoiceProcessingToolkit.interfaces import (
    VoiceProcessingManagerInterface,
    WakeWordDetectorInterface,
    TranscriberInterface,
    AudioRecorderInterface
)
from VoiceProcessingToolkit.transcription.elevenlabs import ElevenLabsTranscriber
from VoiceProcessingToolkit.wake_word_detector.AudioStreamManager import AudioStream
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager
from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
from VoiceProcessingToolkit.shared_resources import thread_manager
from VoiceProcessingToolkit.config import default_config

logger = logging.getLogger(__name__)

class VoiceProcessingManager(VoiceProcessingManagerInterface):
    """
    A manager that coordinates wake word detection, voice recording,
    and transcription to process voice commands.
    
    Attributes:
        wake_word_detector (WakeWordDetectorInterface): The wake word detector instance.
        voice_recorder (AudioRecorderInterface): The voice recorder instance.
        transcriber (TranscriberInterface): The transcriber instance.
        output_dir (str): Directory for saving recordings.
        logger (logging.Logger): Logger for this class.
    """
    
    def __init__(
        self,
        wake_word_detector: Optional[WakeWordDetectorInterface] = None,
        voice_recorder: Optional[AudioRecorderInterface] = None,
        transcriber: Optional[TranscriberInterface] = None,
        output_dir: Optional[str] = None,
        access_key: Optional[str] = None,
        wake_word: Optional[str] = None,
        sensitivity: Optional[float] = None,
        transcriber_api_key: Optional[str] = None
    ):
        """
        Initialize a VoiceProcessingManager with the given components.
        
        Args:
            wake_word_detector: Wake word detector instance. If None, will be created.
            voice_recorder: Voice recorder instance. If None, will be created.
            transcriber: Transcriber instance. If None, will be created.
            output_dir: Directory for saving recordings. If None, uses default from config.
            access_key: Access key for the wake word detector. If None, uses default from config.
            wake_word: Wake word to detect. If None, uses default from config.
            sensitivity: Sensitivity for wake word detection. If None, uses default from config.
            transcriber_api_key: API key for the transcriber. If None, uses default from config.
        """
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Configuration parameters
        self.output_dir = output_dir or default_config.paths.output_dir
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize components
        self.wake_word_detector = wake_word_detector
        self.voice_recorder = voice_recorder
        self.transcriber = transcriber
        
        # Store initialization parameters for setup
        self._init_params = {
            'access_key': access_key,
            'wake_word': wake_word,
            'sensitivity': sensitivity,
            'transcriber_api_key': transcriber_api_key
        }
        
        # Set up components if not provided
        self.setup()
    
    def setup(self) -> None:
        """
        Initialize the components of the voice processing manager if not already done.
        """
        # Create wake word detector if not provided
        if self.wake_word_detector is None:
            self.logger.info("Creating default wake word detector")
            self.wake_word_detector = WakeWordDetector(
                access_key=self._init_params['access_key'],
                wake_word=self._init_params['wake_word'],
                sensitivity=self._init_params['sensitivity']
            )
        
        # Create voice recorder if not provided
        if self.voice_recorder is None:
            self.logger.info("Creating default voice recorder")
            self.voice_recorder = AudioRecorder(output_dir=self.output_dir)
        
        # Create transcriber if not provided
        if self.transcriber is None:
            self.logger.info("Creating default transcriber")
            self.transcriber = ElevenLabsTranscriber(api_key=self._init_params['transcriber_api_key'])
    
    def run(self, transcription: bool = True) -> Optional[str]:
        """
        Process a voice command by detecting a wake word, recording the command, and optionally transcribing it.
        
        Args:
            transcription: If True, perform transcription on the recording.
            
        Returns:
            str or None: The transcribed text or None if no valid recording was made.
        """
        self.logger.info("Starting voice processing")
        
        try:
            # First, detect the wake word
            self.logger.info("Waiting for wake word")
            self.wake_word_detector.run_blocking()
            
            # Once wake word is detected, record the voice command
            self.logger.info("Wake word detected, starting recording")
            recording_path = self.voice_recorder.perform_recording()
            
            if not recording_path or not os.path.exists(recording_path):
                self.logger.warning("No valid recording was made")
                return None
            
            self.logger.info(f"Recording saved to: {recording_path}")
            
            # Transcribe the recording if requested
            if transcription and self.transcriber:
                self.logger.info("Transcribing recording")
                transcription_result = self.transcriber.transcribe_audio(recording_path)
                
                if transcription_result:
                    self.logger.info(f"Transcription result: {transcription_result}")
                    return transcription_result
                else:
                    self.logger.warning("Transcription failed or returned empty result")
            
            # If no transcription was requested or it failed, return the recording path
            return recording_path
            
        except Exception as e:
            self.logger.error(f"Error during voice processing: {e}")
            return None
        finally:
            # Make sure resources are cleaned up
            self.cleanup()
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the voice processing manager.
        """
        try:
            if self.wake_word_detector:
                self.wake_word_detector.cleanup()
            
            if self.voice_recorder:
                self.voice_recorder.cleanup()
                
            self.logger.info("Voice processing resources cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    @classmethod
    def create_default_instance(cls, **kwargs) -> 'VoiceProcessingManagerInterface':
        """
        Create a default instance of the voice processing manager with default configurations.
        
        Args:
            **kwargs: Additional arguments to override default configurations.
            
        Returns:
            VoiceProcessingManagerInterface: A new instance with default or overridden settings.
        """
        # Create a new instance with the given settings
        return cls(**kwargs)
    
    def __del__(self):
        """Ensure cleanup when the object is garbage collected."""
        self.cleanup()

    def monitor_active_threads(self):
        """
        Monitors and logs the status of active threads every second.
        """
        try:
            while True:
                active_threads = threading.enumerate()
                logger.info(f"Active threads: {len(active_threads)}")
                for thread in active_threads:
                    logger.info(f"Thread {thread.name} is {'alive' if thread.is_alive() else 'not alive'}.")
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Thread monitoring interrupted by user.")

    def is_stream_closed(self):
        """
        Checks if the audio stream is closed.

        Returns:
            bool: True if the stream is closed, False otherwise.
        """
        return self.audio_stream_manager.is_stream_closed()

    def reinitialize_stream(self):
        """
        Reinitializes the audio stream if it has been closed.
        """
        if self.is_stream_closed():
            self.audio_stream_manager.initialize_stream(self.rate, self.channels, self.audio_format, self.frames_per_buffer)

    def process_voice_command(self):
        """
        Processes a voice command using the configured components. It starts with wake word detection, followed by voice recording and transcription.

        Returns:
            str or None: The transcribed text of the voice command, or None if no valid recording was made.
        """
        self.wake_word_detector.run_blocking()

        # Once wake word is detected, start recording
        self.voice_recorder.perform_recording()
        # Wait for the recording to complete
        if self.voice_recorder.recording_thread:
            self.voice_recorder.recording_thread.join()

        # If a recording was made, transcribe it
        if self.voice_recorder.last_saved_file is not None:
            # where the transcrition file recorded is stored
            transcription = self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
            logger.info(f"Transcription: {transcription}")
            return transcription

        return None
