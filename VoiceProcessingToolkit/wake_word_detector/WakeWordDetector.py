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
        wake_word='jarvis',
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
import struct
import threading
import time
import wave
from pathlib import Path

import pvporcupine
import pyaudio
from dotenv import load_dotenv

from shared_resources import shutdown_flag
from wake_word_detector.AudioStreamManager import AudioStream
from wake_word_detector.NotificationSoundManager import NotificationSoundManager
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
        __init__(self, access_key, wake_word, sensitivity, action_manager, audio_stream_manager, play_notification_sound):
            Initializes the WakeWordDetector with provided parameters.

        initialize_porcupine(self):
            Initializes the Porcupine engine.

        voice_loop(self):
            Listens for the wake word and triggers actions upon detection.

        run(self):
            Starts the wake word detection in a separate thread.

        cleanup(self):
            Cleans up resources.

        # Additional method documentation...
    """

    def __init__(self, access_key: str, wake_word: str, sensitivity: float,
                 action_manager: ActionManager, audio_stream_manager: AudioStream,
                 play_notification_sound: bool = True, save_audio_directory: str = None,
                 snippet_length: float = 3.0) -> None:
        """
                Initializes the WakeWordDetector with the specified parameters.
        Args:
            access_key (str): Access key for Porcupine.
            wake_word (str): Wake word to detect.
            sensitivity (float): Detection sensitivity.
            action_manager (ActionManager): Manages actions to execute on detection.
            audio_stream_manager (AudioStreamManager): Manages audio stream.
            play_notification_sound (bool): Flag to play a sound on detection.
            save_audio_directory (str): Directory to save audio snippets upon detection.
            snippet_length (float): Length of the audio snippet to save after wake word detection in seconds.

        Raises:
            ValueError: If any initialization parameter is invalid.
        """
        # Determine the path of the notification sound relative to this file's location
        self._snippet_frame_count = None
        notification_sound_path = Path(__file__).parent / 'Wav_MP3' / 'notification.wav'
        if not notification_sound_path.exists():
            raise FileNotFoundError("Notification sound file not found at expected path.")
        self._pre_buffer_time = 1  # Time in seconds to save before wake word
        self._post_buffer_time = 1.5  # Time in seconds to save after wake word
        self._notification_sound_manager = NotificationSoundManager(str(notification_sound_path))

        self._action_manager = action_manager
        self._play_notification_sound = play_notification_sound
        self._access_key = access_key if access_key else os.getenv('PICOVOICE_APIKEY')
        self._wake_word = wake_word
        self._sensitivity = sensitivity
        self._audio_stream_manager = audio_stream_manager
        self._stop_event = threading.Event()
        self._porcupine = None
        self._py_audio = None
        self._snippet_length = snippet_length
        self.initialize_porcupine()
        self.is_running = False  # New attribute
        self._save_audio_directory = save_audio_directory
        if self._save_audio_directory and not os.path.exists(self._save_audio_directory):
            os.makedirs(self._save_audio_directory)

    def initialize_porcupine(self) -> None:
        """
        Initializes the Porcupine wake word engine.
        """
        try:
            if self._porcupine is None:
                self._porcupine = pvporcupine.create(access_key=self._access_key, keywords=[self._wake_word],
                                                     sensitivities=[self._sensitivity])
                self._snippet_frame_count = int(self._porcupine.sample_rate * self._snippet_length)
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
                pcm = self._audio_stream_manager.read()
                pcm = struct.unpack_from("h" * self._porcupine.frame_length, pcm)
                if self._porcupine.process(pcm) >= 0:
                    self.handle_wake_word_detection()

        except Exception as e:
            logger.exception("An error occurred during wake word detection.", exc_info=e)
        finally:
            self.is_running = False

    def handle_wake_word_detection(self):
        """
        Handle the detection of the wake word, play the notification sound, trigger actions, and then stop.
        """
        # Play the notification sound in a non-blocking manner
        if self._play_notification_sound:
            sound_thread = threading.Thread(target=self._notification_sound_manager.play)
            sound_thread.start()
        if self._save_audio_directory:
            pre_detection_frames = int(self._porcupine.sample_rate * self._pre_buffer_time)
            post_detection_frames = int(self._porcupine.sample_rate * self._post_buffer_time)
            save_thread = threading.Thread(target=self.save_audio_snippet,
                                           args=(pre_detection_frames, post_detection_frames))
            save_thread.start()
        action_thread = threading.Thread(target=lambda: asyncio.run(self._action_manager.execute_actions()))
        action_thread.start()
        # Do not set the stop event here to allow continuous detection

    def save_audio_snippet(self, pre_detection_frames: int, post_detection_frames: int):
        """
        Saves a snippet of audio from the buffer to the specified directory.
        """
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"wake_word_{timestamp}.wav"
        filepath = os.path.join(self._save_audio_directory, filename)
        buffer = self._audio_stream_manager.get_rolling_buffer()

        # Calculate the start and end indices for the snippet
        end_index = len(buffer)
        start_index = max(end_index - (pre_detection_frames + post_detection_frames + self._porcupine.frame_length) * 2,
                          0)  # 2 bytes per frame (16-bit audio)
        snippet_buffer = buffer[start_index:end_index]

        with wave.open(filepath, 'wb') as wave_file:
            wave_file.setnchannels(1)
            wave_file.setsampwidth(self._py_audio.get_sample_size(pyaudio.paInt16) if self._py_audio else 2)
            wave_file.setframerate(self._porcupine.sample_rate)
            wave_file.writeframes(snippet_buffer)
            logger.info(f"Saved wake word audio snippet to {filepath}")

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


def main():
    logging.basicConfig(level=logging.DEBUG)

    load_dotenv()
    # Set up the access key for Porcupine
    access_key = os.getenv('PICOVOICE_APIKEY')

    # Set up the audio stream parameters
    rate = 16000
    channels = 1
    audio_format = pyaudio.paInt16
    frames_per_buffer = 512

    # Set up the wake word parameters
    wake_word = 'jarvis'
    sensitivity = 0.5
    snippet_length = 3.0  # Length of the audio snippet in seconds

    # Set up the directory to save audio snippets
    save_audio_directory = 'saved_audio_snippets'
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
        audio_stream_manager=audio_stream_manager,
        play_notification_sound=True,
        save_audio_directory=save_audio_directory,
        snippet_length=snippet_length
    )

    # Run the wake word detector
    print("Listening for wake word...")
    detector.run_blocking()


if __name__ == '__main__':
    main()
