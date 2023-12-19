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

import os
import struct
import threading
import time

import pvporcupine
import pyaudio

from AudioStreamManager import AudioStreamManager
from NotificationSoundManager import NotificationSoundManager


class WakeWordDetector:
    """
    Main class for wake word detection.

    Attributes:
        access_key (str): The access key for the Porcupine wake word engine.
        wake_word (str): The wake word that the detector should listen for.
        sensitivity (float): The sensitivity of the wake word detection.
        action_function (callable): The function to call when the wake word is detected.
        audio_stream_manager (AudioStreamManager): Manages the audio stream.
        notification_sound_manager (object): An object with a play method that plays a notification sound.
        stop_event (threading.Event): Signals when to stop the detection loop.
        porcupine (pvporcupine.Porcupine): The Porcupine wake word engine instance.

    Methods:
        __init__(self, access_key: str, wake_word: str, sensitivity: float,
                 action_function: callable, audio_stream_manager: AudioStreamManager,
                 notification_sound_manager: NotificationSoundManager, continuous_run: bool = False) -> None
            Initializes the WakeWordDetector with the provided parameters.

        initialize_porcupine(self) -> None
            Initializes the Porcupine wake word engine.

        voice_loop(self)
            The main loop that listens for the wake word and triggers the action function.

        run(self) -> None
            Starts the wake word detection loop.

        cleanup(self) -> None
            Cleans up the resources used by the wake word detector.
    """

    def __init__(self, access_key: str, wake_word: str, sensitivity: float,
                 action_function: callable, audio_stream_manager: AudioStreamManager,
                 ) -> None:
        """
        Initializes the WakeWordDetector with the provided parameters.
        
        Args:
            access_key (str): The access key for the Porcupine wake word engine.
            wake_word (str): The wake word that the detector should listen for.
            sensitivity (float): The sensitivity of the wake word detection, between 0 and 1.
            action_function (callable): The function to call when the wake word is detected.
            audio_stream_manager (AudioStreamManager): Manages the audio stream.
        """
        self.access_key = access_key if access_key else os.getenv('PICOVOICE_APIKEY')
        self.wake_word = wake_word
        self.sensitivity = sensitivity
        self.action_function = action_function
        self.audio_stream_manager = audio_stream_manager
        self.stop_event = threading.Event()
        self.porcupine = None
        self.initialize_porcupine()

    def initialize_porcupine(self) -> None:
        """
        Initializes the Porcupine wake word engine.
        """
        if self.porcupine is None:
            self.porcupine = pvporcupine.create(access_key=self.access_key, keywords=[self.wake_word],
                                                sensitivities=[self.sensitivity])

    def voice_loop(self):
        """
        The main loop that listens for the wake word and triggers the action function.
        """
        while not self.stop_event.is_set():
            pcm = self.audio_stream_manager.get_stream().read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            if self.porcupine.process(pcm) >= 0:
                if self.action_function:
                    self.action_function()
                # The notification sound line has been removed
                self.stop_event.set()  # Stop the loop after the wake word is detected

    def run(self) -> None:
        """
        Starts the wake word detection loop.
        """
        detection_thread = threading.Thread(target=self.voice_loop)
        detection_thread.start()
        detection_thread.join()  # Wait for the thread to finish
        self.cleanup()  # Cleanup resources after the thread has finished

    def cleanup(self) -> None:
        """
        Cleans up the resources used by the wake word detector.
        """
        self.audio_stream_manager.cleanup()
        self.porcupine.delete()


def example_usage():
    # Define a simple action function that plays a notification sound and prints a message
    def action_with_notification():
        # Create an instance of NotificationSoundManager with the path to the notification sound
        notification_path = os.path.join(os.path.dirname(__file__), 'Wav_MP3', 'notification.wav')
        notification_sound_manager = NotificationSoundManager(notification_path)
        notification_sound_manager.play()
        print("The wake word was detected!")
        time.sleep(0.45)  # Wait for the wake word to finish playing


    # Set up the required parameters for AudioStreamManager
    rate = 16000  # Sample rate
    channels = 1  # Number of audio channels
    format = pyaudio.paInt16  # Audio format
    frames_per_buffer = 512  # Number of frames per buffer

    # Create an instance of AudioStreamManager
    audio_stream_manager = AudioStreamManager(rate, channels, format, frames_per_buffer)

    # Create an instance of WakeWordDetector
    detector = WakeWordDetector(
        access_key="b2UbNJ2N5xNROBsICABolmKQwtQN7ARTRTSB+U0lZg+kDieYqcx7nw==",
        wake_word='jarvis',
        sensitivity=0.75,
        action_function=action_with_notification,
        audio_stream_manager=audio_stream_manager
    )

    # Start the wake word detection loop
    detector.run()

example_usage()
