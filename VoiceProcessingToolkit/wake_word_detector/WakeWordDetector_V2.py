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

import pvporcupine

from .AudioStreamManager import AudioStreamManager
from .NotificationSoundManager import NotificationSoundManager


class WakeWordDetector:
    """
    Main class for wake word detection.

    Attributes:
        access_key (str): The access key for the Porcupine wake word engine.
        wake_word (str): The wake word that the detector should listen for.
        sensitivity (float): The sensitivity of the wake word detection.
        action_function (callable): The function to call when the wake word is detected.
        audio_stream_manager (AudioStreamManager): Manages the audio stream.
        notification_sound_manager (NotificationSoundManager): Plays a notification sound.
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
                 notification_sound_manager: NotificationSoundManager) -> None:
        """
        Initializes the WakeWordDetector with the provided parameters.
        
        Args:
            access_key (str): The access key for the Porcupine wake word engine.
            wake_word (str): The wake word that the detector should listen for.
            sensitivity (float): The sensitivity of the wake word detection, between 0 and 1.
            action_function (callable): The function to call when the wake word is detected.
            audio_stream_manager (AudioStreamManager): Manages the audio stream.
            notification_sound_manager (NotificationSoundManager): Plays a notification sound.
        """
        self.access_key = access_key if access_key else os.getenv('PICOVOICE_APIKEY')
        self.wake_word = wake_word
        self.sensitivity = sensitivity
        self.action_function = action_function
        self.audio_stream_manager = audio_stream_manager
        self.notification_sound_manager = notification_sound_manager
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
                self.notification_sound_manager.play()
                if self.action_function:
                    self.action_function()

    def run(self) -> None:
        """
        Starts the wake word detection loop.
        """
        self.voice_loop()
        self.cleanup()

    def cleanup(self) -> None:
        """
        Cleans up the resources used by the wake word detector.
        """
        self.audio_stream_manager.cleanup()
        self.porcupine.delete()


def custom_action():
    print("Wake word detected!")