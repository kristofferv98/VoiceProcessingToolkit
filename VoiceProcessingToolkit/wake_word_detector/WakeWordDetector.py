"""
WakeWordDetector
------------------------

This module provides an interface for wake word detection using the Porcupine engine. It includes classes for managing
audio streams and notification sounds, and executing actions upon wake word detection.

Before using, set the PICOVOICE_APIKEY environment variable with your Porcupine access key.

Classes:
    WakeWordDetector: Detects specified wake words and manages actions upon detection.
    AudioStreamManager: Manages audio stream from the microphone.
    NotificationSoundManager: Plays notification sounds.
    ActionManager: Manages and executes actions based on wake word detection.

Example:
    ```python
    from wake_word_detector import WakeWordDetector, AudioStreamManager, NotificationSoundManager

    audio_stream_manager = AudioStreamManager(rate, channels, format, frames_per_buffer)
    notification_sound_manager = NotificationSoundManager('path/to/sound.wav')
    detector = WakeWordDetector(
        access_key='your-picovoice-api-key',
        wake_word='computer',
        sensitivity=0.5,
        action_manager=custom_action,
        audio_stream_manager=audio_stream_manager,
        play_notification_sound=True
    )
    detector.run()
    ```
"""

import asyncio
import logging
import os
from importlib import resources

import struct
import threading
import time
import wave

import pvporcupine
import pyaudio
from dotenv import load_dotenv
from typing import Optional, List, Callable, Any

import pvporcupine
import pyaudio
from VoiceProcessingToolkit.interfaces import WakeWordDetectorInterface, AudioStreamInterface
from VoiceProcessingToolkit.wake_word_detector.AudioStreamManager import AudioStream
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager
from VoiceProcessingToolkit.shared_resources import shutdown_flag, thread_manager
from VoiceProcessingToolkit.config import default_config

logger = logging.getLogger(__name__)


class NotificationSoundManager:
    """
    Manages the playback of notification sounds.
    
    Attributes:
        sound_file_path (str): Path to the notification sound file.
        logger (logging.Logger): Logger for this class.
        pyaudio_instance (pyaudio.PyAudio): Instance of PyAudio for playback.
    """
    
    def __init__(self, sound_file_path: str = None):
        """
        Initialize a new NotificationSoundManager.
        
        Args:
            sound_file_path (str, optional): Path to the notification sound file.
                                             If None, uses the default from config.
        """
        self.sound_file_path = sound_file_path or default_config.wake_word.notification_sound_path
        self.logger = logging.getLogger(__name__)
        self.pyaudio_instance: Optional[pyaudio.PyAudio] = None
        
        if self.sound_file_path and not os.path.exists(self.sound_file_path):
            self.logger.warning(f"Notification sound file not found: {self.sound_file_path}")
    
    def play_notification(self) -> bool:
        """
        Play the notification sound.
        
        Returns:
            bool: True if the sound was played successfully, False otherwise.
        """
        if not self.sound_file_path or not os.path.exists(self.sound_file_path):
            self.logger.warning("Cannot play notification: sound file not found")
            return False
        
        try:
            import wave
            
            # Initialize PyAudio if needed
            if self.pyaudio_instance is None:
                self.pyaudio_instance = pyaudio.PyAudio()
            
            with wave.open(self.sound_file_path, 'rb') as wave_file:
                # Open a stream for playback
                stream = self.pyaudio_instance.open(
                    format=self.pyaudio_instance.get_format_from_width(wave_file.getsampwidth()),
                    channels=wave_file.getnchannels(),
                    rate=wave_file.getframerate(),
                    output=True
                )
                
                # Read and play chunks of data
                chunk_size = 1024
                data = wave_file.readframes(chunk_size)
                
                while data:
                    stream.write(data)
                    data = wave_file.readframes(chunk_size)
                
                # Close the stream
                stream.stop_stream()
                stream.close()
                
                self.logger.debug("Notification sound played successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Error playing notification sound: {e}")
            return False
    
    def cleanup(self) -> None:
        """Clean up resources used by the NotificationSoundManager."""
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except Exception as e:
                self.logger.warning(f"Error terminating PyAudio: {e}")
            finally:
                self.pyaudio_instance = None


class WakeWordDetector(WakeWordDetectorInterface):
    """
    Listens for a wake word and triggers actions when detected.
    Implements the WakeWordDetectorInterface.
    
    Attributes:
        access_key (str): Access key for the Porcupine wake word engine.
        wake_word (str): The wake word to listen for.
        sensitivity (float): Sensitivity for wake word detection (0.0 to 1.0).
        action_manager (ActionManager): Manager for actions to execute on detection.
        notification_manager (NotificationSoundManager): Manager for playing notifications.
        audio_stream (AudioStreamInterface): Audio stream for capturing audio.
        porcupine (pvporcupine.Porcupine): Porcupine wake word detection engine.
        is_running (bool): Flag indicating if the detector is running.
        detection_thread (threading.Thread): Thread for wake word detection.
        logger (logging.Logger): Logger for this class.
    """
    
    def __init__(
        self,
        access_key: Optional[str] = None,
        wake_word: Optional[str] = None,
        sensitivity: Optional[float] = None,
        action_manager: Optional[ActionManager] = None,
        notification_sound_path: Optional[str] = None,
        audio_stream: Optional[AudioStreamInterface] = None
    ):
        """
        Initialize a new WakeWordDetector.
        
        Args:
            access_key: Access key for Porcupine. If None, uses environment variable or config.
            wake_word: Wake word to detect. If None, uses default from config.
            sensitivity: Detection sensitivity (0.0 to 1.0). If None, uses default from config.
            action_manager: Manager for actions to execute on detection. If None, creates a new one.
            notification_sound_path: Path to notification sound file. If None, uses default from config.
            audio_stream: Audio stream to use. If None, creates a new one.
        """
        # Initialize configuration
        wake_word_config = default_config.wake_word
        self.access_key = access_key or os.getenv('PORCUPINE_ACCESS_KEY') or wake_word_config.access_key
        self.wake_word = wake_word or wake_word_config.wake_word
        self.sensitivity = sensitivity if sensitivity is not None else wake_word_config.sensitivity
        
        # Initialize components
        self.action_manager = action_manager or ActionManager()
        self.notification_manager = NotificationSoundManager(notification_sound_path)
        self.audio_stream = audio_stream
        
        # State management
        self.porcupine = None
        self.is_running = False
        self.detection_thread = None
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        if not self.access_key:
            self.logger.warning("No Porcupine access key provided. Wake word detection will not work.")
    
    def run(self) -> None:
        """
        Start the wake word detection in a non-blocking way.
        Creates a daemon thread for detection.
        """
        if self.is_running:
            self.logger.warning("Wake word detector is already running")
            return
        
        # Create and start the detection thread
        self.detection_thread = thread_manager.create_daemon_thread(
            target=self.run_blocking,
            name="WakeWordDetectionThread"
        )
        self.detection_thread.start()
        self.logger.info("Wake word detection started in background thread")
    
    def run_blocking(self) -> None:
        """
        Start the wake word detection and block until detection occurs or shutdown is requested.
        """
        if self.is_running:
            self.logger.warning("Wake word detector is already running")
            return
        
        try:
            self._initialize_detection()
            self._voice_loop()
        except Exception as e:
            self.logger.error(f"Error in wake word detection: {e}")
        finally:
            self.cleanup()
    
    def _initialize_detection(self) -> None:
        """
        Initialize the wake word detection components.
        
        Raises:
            RuntimeError: If initialization fails.
        """
        try:
            # Initialize the wake word engine (Porcupine)
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=[self.wake_word],
                sensitivities=[self.sensitivity]
            )
            
            # Initialize audio stream if not provided
            if self.audio_stream is None:
                self.audio_stream = AudioStream(
                    rolling_buffer_size=self.porcupine.frame_length * 2
                )
                self.audio_stream.initialize_stream(
                    rate=self.porcupine.sample_rate,
                    channels=1,
                    audio_format=pyaudio.paInt16,
                    frames_per_buffer=self.porcupine.frame_length
                )
            
            self.is_running = True
            self.logger.info(f"Wake word detector initialized with wake word '{self.wake_word}' "
                             f"and sensitivity {self.sensitivity}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize wake word detection: {e}")
            self.cleanup()
            raise RuntimeError(f"Failed to initialize wake word detection: {e}")
    
    def _voice_loop(self) -> None:
        """
        Main detection loop that processes audio and detects the wake word.
        """
        if not self.is_running or not self.porcupine or not self.audio_stream:
            self.logger.error("Cannot start voice loop: detection not properly initialized")
            return
        
        self.logger.info("Starting wake word detection loop")
        
        while self.is_running and not thread_manager.is_shutdown_requested():
            try:
                # Read audio data
                pcm = self.audio_stream.read()
                
                # Process audio with Porcupine
                result = self.porcupine.process(pcm)
                
                # Check if wake word was detected
                if result >= 0:
                    self.logger.info(f"Wake word '{self.wake_word}' detected!")
                    
                    # Play notification sound if configured
                    self.notification_manager.play_notification()
                    
                    # Execute registered actions
                    if self.action_manager:
                        try:
                            # Use an async event loop to execute actions
                            import asyncio
                            asyncio.run(self.action_manager.execute_actions())
                        except Exception as e:
                            self.logger.error(f"Error executing actions: {e}")
                
            except KeyboardInterrupt:
                self.logger.info("Keyboard interrupt detected in voice loop")
                break
            except Exception as e:
                self.logger.error(f"Error in voice detection loop: {e}")
                # Sleep briefly to avoid CPU spinning on repeated errors
                time.sleep(0.1)
        
        self.logger.info("Voice detection loop ended")
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the wake word detector.
        Can be called multiple times safely.
        """
        self.is_running = False
        
        # Clean up Porcupine
        if self.porcupine:
            try:
                self.porcupine.delete()
                self.logger.debug("Porcupine engine deleted")
            except Exception as e:
                self.logger.warning(f"Error cleaning up Porcupine: {e}")
            finally:
                self.porcupine = None
        
        # Clean up audio stream
        if self.audio_stream:
            try:
                self.audio_stream.cleanup()
                self.logger.debug("Audio stream cleaned up")
            except Exception as e:
                self.logger.warning(f"Error cleaning up audio stream: {e}")
            
        # Clean up notification manager
        if hasattr(self, 'notification_manager'):
            try:
                self.notification_manager.cleanup()
                self.logger.debug("Notification manager cleaned up")
            except Exception as e:
                self.logger.warning(f"Error cleaning up notification manager: {e}")
        
        self.logger.info("Wake word detector resources cleaned up")
    
    def __del__(self):
        """Ensure cleanup when the object is garbage collected."""
        self.cleanup()


def main():
    logging.basicConfig(level=logging.DEBUG)

    load_dotenv()
    load_dotenv()
    # Set up the access key for Porcupine
    access_key = os.getenv('PICOVOICE_APIKEY')

    # Set up the audio stream parameters
    rate = 16000
    channels = 1
    audio_format = pyaudio.paInt16
    frames_per_buffer = 512

    # Set up the wake word parameters
    wake_word = 'computer'
    sensitivity = 0.5
    snippet_length = 3.0  # Length of the audio snippet in seconds

    # Set up the directory to save audio snippets
    save_audio_directory = 'wake_word_output'
    if not os.path.exists(save_audio_directory):
        os.makedirs(save_audio_directory)

    # Initialize the audio stream manager
    audio_stream_manager = AudioStream(rate, channels, audio_format, frames_per_buffer)

    # Initialize the action manager
    action_manager = ActionManager()

    # Initialize the wake word detector
    detector = WakeWordDetector(
        access_key=access_key,
        wake_word=wake_word,
        sensitivity=sensitivity,
        action_manager=action_manager,
        audio_stream=audio_stream_manager
    )

    # Run the wake word detector
    print("Listening for wake word...")
    detector.run_blocking()


if __name__ == '__main__':
    main()
