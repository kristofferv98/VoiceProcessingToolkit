"""
WakeWordDetector Library
------------------------

This module provides an easy-to-use interface for wake word detection and voice transcription using Porcupine and Cobra.

Classes:
    WakeWordDetector: Main class for wake word detection and handling transcription.
    CobraVoiceRecorder: Handles voice recording and transcription using Cobra VAD engine.

How to use:
    1. Set up the required environment variables (PICOVOICE_APIKEY).
    2. Create an instance of WakeWordDetector.
    3. Call the `run` method to start listening for the wake word.

Example:
    ```python
    from wake_word_detector import WakeWordDetector

    detector = WakeWordDetector(picovoice_api_key='your-picovoice_api_key', wake_word='jarvis', run_once=True)
    result = detector.run()
    print("Transcription:", result)
    ```
"""
import contextlib
import logging
import os
import struct
import threading

import pvporcupine
import pyaudio
import pygame
from dotenv import load_dotenv

from .AudioStreamManager import AudioStreamManager

logger = logging.getLogger(__name__)

load_dotenv()





class WakeWordDetector:
    """
    Main class for wake word detection and handling transcription.

    Attributes:
        access_key (str): Access key for Porcupine.
        wake_word (str): Wake word to listen for.
        sensitivity (float): Sensitivity of wake word detection.
        action_function (callable): Custom function to call when wake word is detected.
        notification_sound_path (str): Path to notification sound file.
        continuous_run (bool): Whether to run the detection loop continuously.

    Methods:
        run: Starts the wake word detection loop and returns the transcription result.
    """

    def __init__(self, access_key: str = None, wake_word: str = "jarvis",
                 sensitivity: float = 0.75, action_function: callable = None,
                 notification_sound_path: str = None, continuous_run: bool = False) -> None:
        """
        Initializes the WakeWordDetector with the provided parameters.

        Args:
            access_key (str): Access key for Porcupine, can be provided or set as an environment variable 'PICOVOICE_APIKEY'.
            wake_word (str): Wake word to listen for.
            sensitivity (float): Sensitivity of wake word detection.
            action_function (callable): Custom function to call when wake word is detected.
            notification_sound_path (str): Path to notification sound file.
            continuous_run (bool): Whether to run the detection loop continuously.
        """
        self.continuous_run = continuous_run
        self.notification_sound = None
        self.audio_stream = None
        self.py_audio = None
        self.porcupine = None
        self.access_key = access_key if access_key is not None else os.getenv('PICOVOICE_APIKEY')
        if not self.access_key:
            raise ValueError(
                "Porcupine access key must be provided or set as an environment variable 'PICOVOICE_APIKEY'")
        self.wake_word = wake_word
        self.sensitivity = sensitivity
        self.action_function = action_function
        default_sound_path = os.path.join(os.path.dirname(__file__), 'Wav_MP3', 'notification.wav')
        self.notification_sound_path = notification_sound_path or default_sound_path
        self.stop_event = threading.Event()  # Initialize the stop event
        self.initialize_porcupine()
        self.initialize_audio_stream()
        self.initialize_notification_sound()

    def initialize_porcupine(self) -> None:
        self.porcupine = pvporcupine.create(access_key=self.access_key, keywords=[self.wake_word],
                                            sensitivities=[self.sensitivity])
        logger.debug("Porcupine initialized with wake word '%s' and sensitivity %.2f", self.wake_word,
                     self.sensitivity)

    def initialize_audio_stream(self) -> None:
        if hasattr(self, 'audio_stream') and self.audio_stream:
            self.audio_stream.close()
        self.audio_stream_manager = AudioStreamManager(rate=self.porcupine.sample_rate,
                                                       channels=1,
                                                       format=pyaudio.paInt16,
                                                       frames_per_buffer=self.porcupine.frame_length)
        self.audio_stream = self.audio_stream_manager.get_stream()

    def initialize_notification_sound(self) -> None:
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            pygame.mixer.init()
        try:
            self.notification_sound = pygame.mixer.Sound(self.notification_sound_path)
            self.notification_sound.set_volume(0.3)
            logging.debug("Notification sound initialized with volume 0.3")
        except pygame.error as e:
            logging.error("Failed to load notification sound: %s", e)
            logging.debug("Notification sound path: %s", self.notification_sound_path)
            raise

    def voice_loop(self) -> str:
        frame_count = 0
        transcription_text = None  # Declare it here to use throughout the method

        while not self.stop_event.is_set():
            try:
                pcm = self.audio_stream.read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                if self.porcupine.process(pcm) >= 0:
                    self.notification_sound.play()
                    logging.info("Wake word detected")

                    # Determine the correct function to call
                    if self.action_function and callable(self.action_function):
                        self.action_function()

                    if self.continuous_run:
                        continue  # Continue the loop for continuous run
                    else:
                        return transcription_text  # Return the result and break out of the loop

                frame_count += 1
            except Exception as e:
                logging.exception("Error in voice loop: %s", e)
                self.initialize_audio_stream()

        return transcription_text  # Return the result after the loop


    def cleanup(self) -> None:
        self.audio_stream_manager.cleanup()
        self.porcupine.delete()

    def run(self) -> str:
        """
        Starts the wake word detection loop and returns the transcription result.

        Returns:
            str: The transcription result or None if no transcription was obtained.
        """
        logging.info("Listening for the wake word...")
        return self.voice_loop()  # Return the result of voice_loop


def custom_action():
    picovoice_api_key = os.getenv('PICOVOICE_APIKEY')
    voice_detector = WakeWordDetector(access_key=picovoice_api_key, action_function=custom_action)
    transcription_text = voice_detector.voice_loop()
    voice_detector.cleanup()
    if transcription_text:
        print("Wake word detected! Transcription result:", transcription_text)
    else:
        print("Wake word detected! No transcription obtained.")
    return transcription_text
class AudioStreamManager:
    def __init__(self, rate: int, channels: int, format: int, frames_per_buffer: int):
        self.py_audio = pyaudio.PyAudio()
        self.stream = self._initialize_stream(rate, channels, format, frames_per_buffer)

    def _initialize_stream(self, rate: int, channels: int, format: int, frames_per_buffer: int):
        try:
            return self.py_audio.open(rate=rate, channels=channels, format=format,
                                      input=True, frames_per_buffer=frames_per_buffer)
        except Exception as e:
            logging.error("Failed to initialize audio stream: %s", e)
            raise

    def get_stream(self):
        return self.stream

    def cleanup(self):
        if self.stream.is_active():
            self.stream.stop_stream()
        self.stream.close()
        self.py_audio.terminate()
