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
from typing import Any

import pvporcupine
import pyaudio
import pygame
from dotenv import load_dotenv

from VoiceProcessingToolkit.voice_detection import CobraVoiceRecorder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from a .env file if available
load_dotenv()


def record_and_transcribe(wake_word: str = 'jarvis', sensitivity: float = 0.75,
                          notification_sound_path: str = None) -> str:
    """
    A simplified function to perform a single run of wake word detection and transcription.

    Args:
        wake_word (str): The wake word to listen for.
        sensitivity (float): The sensitivity of wake word detection.
        notification_sound_path (str): Path to the notification sound file.

    Returns:
        str: The transcription result or None if no transcription was obtained.
    """
    picovoice_api_key = os.getenv('PICOVOICE_APIKEY', 'picovoice_api_key')

    # Initialize and run the WakeWordDetector for a single transcription
    detector = WakeWordDetector(
        picovoice_api_key=picovoice_api_key,
        wake_word=wake_word,
        sensitivity=sensitivity,
        notification_sound_path=notification_sound_path,
        continuous_run=False
    )

    transcription_result = detector.run()
    detector.cleanup()
    return transcription_result



class WakeWordDetector:
    """
    Main class for wake word detection and handling transcription.

    Attributes:
        picovoice_api_key (str): Access key for Porcupine.
        wake_word (str): Wake word to listen for.
        sensitivity (float): Sensitivity of wake word detection.
        action_function (callable): Custom function to call when wake word is detected.
        notification_sound_path (str): Path to notification sound file.
        continuous_run (bool): Whether to run the detection loop continuously.
        transcription_function (callable): Function to call for transcribing after wake word detection.

    Methods:
        run: Starts the wake word detection loop and returns the transcription result.
    """

    def __init__(self, picovoice_api_key: str = None, wake_word: str = "jarvis",
                 sensitivity: float = 0.75, action_function: callable = None,
                 notification_sound_path: str = None, continuous_run: bool = False,
                 transcription_function: callable = None) -> None:
        """
        Initializes the WakeWordDetector with the provided parameters.

        Args:
            picovoice_api_key (str): Access key for Porcupine.
            wake_word (str): Wake word to listen for.
            sensitivity (float): Sensitivity of wake word detection.
            action_function (callable): Custom function to call when wake word is detected.
            notification_sound_path (str): Path to notification sound file.
            continuous_run (bool): Whether to run the detection loop continuously.
            transcription_function (callable): Function to call for transcribing after wake word detection.
        """
        self.transcription_function = transcription_function or self.default_transcription_action
        self.continuous_run = continuous_run
        self.notification_sound = None
        self.audio_stream = None
        self.py_audio = None
        self.porcupine = None
        # The API key for Porcupine can be provided as an argument or set as an environment variable 'PICOVOICE_APIKEY'.
        self.picovoice_api_key = picovoice_api_key if picovoice_api_key is not None else os.getenv('PICOVOICE_APIKEY')
        if not self.picovoice_api_key:
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
        self.porcupine = pvporcupine.create(access_key=self.picovoice_api_key, keywords=[self.wake_word],
                                            sensitivities=[self.sensitivity])
        logger.debug("Porcupine initialized with wake word '%s' and sensitivity %.2f", self.wake_word,
                     self.sensitivity)

    def initialize_audio_stream(self) -> None:
        if hasattr(self, 'audio_stream') and self.audio_stream:
            self.audio_stream.close()
        self.py_audio = pyaudio.PyAudio()
        try:
            self.audio_stream = self.py_audio.open(rate=self.porcupine.sample_rate, channels=1, format=pyaudio.paInt16,
                                                   input=True, frames_per_buffer=self.porcupine.frame_length)
        except Exception as e:
            logging.error("Failed to initialize audio stream: %s", e)
            logging.debug(
                "Audio stream initialization parameters: rate=%d, channels=%d, format=%s, input=%s, "
                "frames_per_buffer=%d",
                self.porcupine.sample_rate, 1, pyaudio.paInt16, True, self.porcupine.frame_length)
            raise

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
                        transcription_text = self.action_function()
                    else:
                        transcription_text = self.transcription_function()

                    if self.continuous_run:
                        continue  # Continue the loop for continuous run
                    else:
                        return transcription_text  # Return the result and break out of the loop

                frame_count += 1
            except Exception as e:
                logging.exception("Error in voice loop: %s", e)
                self.initialize_audio_stream()

        return transcription_text  # Return the result after the loop

    def default_transcription_action(self) -> Any | None:
        recorder = CobraVoiceRecorder(access_key=self.picovoice_api_key)
        transcription_text = recorder.start_recording()  # Start recording and get transcription
        if transcription_text:
            logging.info("Transcription obtained")
            logging.debug("Transcription Result: %s", transcription_text)
            return transcription_text
        else:
            logging.info("No transcription obtained.")
            return None  # Return None if no transcription

    def cleanup(self) -> None:
        if self.audio_stream.is_active():
            self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.py_audio.terminate()
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
    voice_detector = WakeWordDetector(picovoice_api_key=picovoice_api_key, action_function=custom_action)
    transcription_text = voice_detector.voice_loop()
    voice_detector.cleanup()
    if transcription_text:
        print("Wake word detected! Transcription result:", transcription_text)
    else:
        print("Wake word detected! No transcription obtained.")
    return transcription_text
