
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
        ...

    Methods:
        ...
    """

    def __init__(self, access_key: str, wake_word: str, sensitivity: float, 
                 action_function: callable, audio_stream_manager: AudioStreamManager, 
                 notification_sound_manager: NotificationSoundManager) -> None:
        """
        Initializes the WakeWordDetector with the provided parameters.
        Args:
            ...
        """
        ...
        self.audio_stream_manager = audio_stream_manager
        self.notification_sound_manager = notification_sound_manager
        ...

    def initialize_porcupine(self) -> None:
        ...
        # Initialization logic for Porcupine
        ...

    def voice_loop(self):
        while not self.stop_event.is_set():
            pcm = self.audio_stream_manager.get_stream().read(self.porcupine.frame_length)
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
            if self.porcupine.process(pcm) >= 0:
                self.notification_sound_manager.play_sound()
                if self.action_function:
                    self.action_function()





def custom_action():
    print("Wake word detected!")
