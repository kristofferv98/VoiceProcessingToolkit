"""
WakeWordDetector Library
------------------------

This module provides an easy-to-use interface for wake word detection using Porcupine.

Classes:
    WakeWordDetector: Main class for wake word detection.
    AudioStreamManager: Manages the audio stream from the microphone.
    NotificationSoundManager: Plays a notification sound.

How to use:
    1. Set up the required environment variables (PICOVOICE_APIKEY).
    2. Create an instance of AudioStreamManager and NotificationSoundManager.
    3. Create an instance of WakeWordDetector.
    4. Call the `run` method to start listening for the wake word.

Example:
    ```python
    from wake_word_detector import WakeWordDetector, AudioStreamManager, NotificationSoundManager

    audio_stream_manager = AudioStreamManager(rate, channels, format, frames_per_buffer)
    notification_sound_manager = NotificationSoundManager('path/to/notification/sound.wav')
    detector = WakeWordDetector(
        access_key='your-picovoice_api_key',
        wake_word='jarvis',
        sensitivity=0.5,
        action_function=custom_action,
        audio_stream_manager=audio_stream_manager,
        notification_sound_manager=notification_sound_manager
    )
    detector.run()
    ```
"""

import asyncio
import logging
import os
import struct
import threading
from VoiceProcessingToolkit.shared_resources import shutdown_flag
import time
import pvporcupine
import pyaudio
from dotenv import load_dotenv

from wake_word_detector.AudioStreamManager import AudioStream
from wake_word_detector.NotificationSoundManager import NotificationSoundManager
from VoiceProcessingToolkit.wake_word_detector.ActionManager import register_action_decorator
from wake_word_detector.ActionManager import ActionManager

logger = logging.getLogger(__name__)



class WakeWordDetector:
    """
    Detects a specified wake word using the Porcupine engine and executes registered actions upon detection.

    Attributes:
        _access_key (str): The access key for the Porcupine wake word engine.
        _wake_word (str): The wake word that the detector should listen for.
        _sensitivity (float): The sensitivity of the wake word detection, between 0 and 1.
        _audio_stream_manager (AudioStreamManager): Manages the audio stream from the microphone.
        _action_manager (ActionManager): Manages the actions to be executed when the wake word is detected.
        _play_notification_sound (bool): Indicates whether to play a notification sound upon detection.
        _stop_event (threading.Event): An event to signal the detection loop to stop.
        _porcupine (pvporcupine.Porcupine): The Porcupine wake word engine instance.

    Methods:
        __init__(self, access_key: str, wake_word: str, sensitivity: float,
                 audio_stream_manager: AudioStreamManager, action_manager: ActionManager,
                 play_notification_sound: bool = True) -> None
            Initializes the WakeWordDetector with the provided parameters.

        initialize_porcupine(self) -> None
            Initializes the Porcupine wake word engine with the specified wake word and sensitivity.

        voice_loop(self)
            The main loop that listens for the wake word and triggers the registered actions.

        run(self) -> None
            Starts the wake word detection loop in a separate thread.

        cleanup(self) -> None
            Cleans up the resources used by the wake word detector, including the audio stream and Porcupine instance.
    """

    def __init__(self, access_key: str, wake_word: str, sensitivity: float,
                 action_manager: ActionManager, audio_stream_manager: AudioStream,
                 play_notification_sound: bool = True) -> None:
        """
        Initializes the WakeWordDetector with the provided parameters.

        Args:
            access_key (str): The access key for the Porcupine wake word engine.
            wake_word (str): The wake word that the detector should listen for.
            sensitivity (float): The sensitivity of the wake word detection, between 0 and 1.
            action_manager (ActionManager): Manages the actions to execute when the wake word is detected.
            audio_stream_manager (AudioStreamManager): Manages the audio stream.
        """
        self._notification_sound_manager = NotificationSoundManager(
            '/Users/kristoffervatnehol/PycharmProjects/VoiceProcessingToolkit/VoiceProcessingToolkit'
            '/wake_word_detector/Wav_MP3/notification.wav')
        self._action_manager = action_manager
        self._play_notification_sound = play_notification_sound
        self._access_key = access_key if access_key else os.getenv('PICOVOICE_APIKEY')
        self._wake_word = wake_word
        self._sensitivity = sensitivity
        self._audio_stream_manager = audio_stream_manager
        self._stop_event = threading.Event()
        self._porcupine = None
        self.initialize_porcupine()
        self.is_running = False  # New attribute


    def initialize_porcupine(self) -> None:
        """
        Initializes the Porcupine wake word engine.
        """
        try:
            if self._porcupine is None:
                self._porcupine = pvporcupine.create(access_key=self._access_key, keywords=[self._wake_word],
                                                     sensitivities=[self._sensitivity])
        except pvporcupine.PorcupineError as e:
            logger.exception("Failed to initialize Porcupine with the given parameters.", exc_info=e)
            raise

    def voice_loop(self):
        """
        The main loop that listens for the wake word and triggers the action function.
        """
        self.is_running = True
        try:
            while not self._stop_event.is_set() and not shutdown_flag.is_set():
                pcm = self._audio_stream_manager.get_stream().read(self._porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self._porcupine.frame_length, pcm)
                if self._porcupine.process(pcm) >= 0:
                    self.handle_wake_word_detection()

        except Exception as e:
            logger.exception("An error occurred during wake word detection.", exc_info=e)
        finally:
            self.is_running = False
        # Check if shutdown flag is set and stop the loop
        if shutdown_flag.is_set():
            self._stop_event.set()

    def handle_wake_word_detection(self):
        """
        Handle the detection of the wake word, play the notification sound, trigger actions, and then stop.
        """
        if self._play_notification_sound:
            self._notification_sound_manager.play()  # This should block until the sound is done playing
        action_thread = threading.Thread(target=lambda: asyncio.run(self._action_manager.execute_actions()))
        action_thread.start()
        self._stop_event.set()  # Signal to stop after handling the detection


    def run(self) -> None:
        """
        Starts the wake word detection loop.
        """
        detection_thread = threading.Thread(target=self.voice_loop)
        detection_thread.start()
        detection_thread.join()  # Wait for the thread to finish
        self.cleanup()  # Cleanup resources after the thread has finished

    def run_blocking(self) -> None:
        """
        Starts the wake word detection loop and waits for it to finish before returning.
        This method is intended to be used when the detection should block the calling thread.
        """
        self.voice_loop()
        self.cleanup()

    def cleanup(self) -> None:
        """
        Cleans up the resources used by the wake word detector.
        """
        self._audio_stream_manager.cleanup()
        self._porcupine.delete()

def example_usage():
    load_dotenv()
    # Set up the required parameters for AudioStreamManager
    rate = 16000  # Sample rate
    channels = 1  # Number of audio channels
    audio_format = pyaudio.paInt16  # Audio format
    frames_per_buffer = 512  # Number of frames per buffer

    # Create an instance of AudioStreamManager
    audio_stream_manager = AudioStream(rate, channels, audio_format, frames_per_buffer)

    # Create an instance of ActionManager
    action_manager = ActionManager()

    @register_action_decorator(action_manager)
    def action_with_notification():
        logger.info("Sync function is running...")
        time.sleep(4.5)
        logger.info("Action function completed!")

    @register_action_decorator(action_manager)
    async def async_action_1():
        logger.info("Async function is running...")
        await asyncio.sleep(1)  # Simulate an async wait
        logger.info("Async function completed!")

    PICOVOICE_APIKEY = os.getenv('PICOVOICE_APIKEY')
    # Create an instance of WakeWordDetector with the ActionManager
    detector = WakeWordDetector(
        access_key=PICOVOICE_APIKEY,
        wake_word='jarvis',
        sensitivity=0.75,
        action_manager=action_manager,
        audio_stream_manager=audio_stream_manager,
        play_notification_sound=True
    )

    # Start the wake word detection loop
    detector.run()


def main():
    logging.basicConfig(level=logging.INFO)
    try:
        example_usage()
    except KeyboardInterrupt:
        logger.info("Wake word detection stopped by user.")
    except Exception as e:
        logger.exception("An error occurred during wake word detection.", exc_info=e)


if __name__ == "__main__":
    main()
