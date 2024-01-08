import contextlib
import logging
import os
import wave

import pygame

logger = logging.getLogger(__name__)


class NotificationSoundManager:
    _mixer_initialized = False

    def __init__(self, sound_file_path: str):
        self.sound_file_path = sound_file_path
        self.notification_sound = None
        if not NotificationSoundManager._mixer_initialized:
            with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
                pygame.mixer.init()
                NotificationSoundManager._mixer_initialized = True
        self._initialize_sound()

    def _initialize_sound(self):
        try:
            self.notification_sound = pygame.mixer.Sound(self.sound_file_path)
            self.notification_sound.set_volume(0.3)
            logger.debug("Notification sound initialized with volume 0.3")
        except pygame.error as e:
            logger.exception("Failed to load notification sound due to Pygame error.", exc_info=e)
            raise
        except Exception as e:
            logger.exception("An unexpected error occurred while initializing the notification sound.", exc_info=e)
            raise

    def play(self, preloaded_sound=None):
        if self.notification_sound:
            self.notification_sound.play()
        if self.notification_sound:
            self.notification_sound.play()
