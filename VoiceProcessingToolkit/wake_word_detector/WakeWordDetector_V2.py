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
    notification_sound_path = 'path/to/notification/sound.wav'  # Replace with actual path
    notification_sound_manager = NotificationSoundManager(notification_sound_path)
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

import struct
import threading
import pvporcupine

from .AudioStreamManager import AudioStreamManager
from .NotificationSoundManager import NotificationSoundManager

    def initialize_porcupine(self) -> None:
        """
        Initializes the Porcupine wake word engine.
        """
        self.porcupine = pvporcupine.create(access_key=self.access_key, keywords=[self.wake_word],
                                            sensitivities=[self.sensitivity])

    def voice_loop(self):
        """
        The main loop that listens for the wake word and triggers the action function.
        Handles exceptions that might occur during audio stream reading and processing.
        """
        try:
            while not self.stop_event.is_set():
                pcm = self.audio_stream_manager.get_stream().read(self.porcupine.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                if self.porcupine.process(pcm) >= 0:
                    self.notification_sound_manager.play()
                    if self.action_function:
                        self.action_function()
                    if not self.continuous_run:
                        break
        except Exception as e:
            logger.error("An error occurred in the voice loop: %s", e)

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

