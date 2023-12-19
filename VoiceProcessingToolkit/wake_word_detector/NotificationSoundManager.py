import contextlib
import logging
import os

import pygame

logger = logging.getLogger(__name__)
import logging

logger = logging.getLogger(__name__)

class NotificationSoundManager:
    def __init__(self, sound_file_path: str):
        self.sound_file_path = sound_file_path
        self.notification_sound = None
        self._initialize_sound()

    def _initialize_sound(self):
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            pygame.mixer.init()
        try:
            self.notification_sound = pygame.mixer.Sound(self.sound_file_path)
            self.notification_sound.set_volume(0.3)
            logger.debug("Notification sound initialized with volume 0.3")
        try:
            with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
                pygame.mixer.init()
            self.notification_sound = pygame.mixer.Sound(self.sound_file_path)
            self.notification_sound.set_volume(0.3)
            logger.debug("Notification sound initialized with volume 0.3")
        except pygame.error as e:
            logger.exception("Failed to load notification sound due to Pygame error.", exc_info=e)
            raise
        except Exception as e:
            logger.exception("An unexpected error occurred while initializing the notification sound.", exc_info=e)
            raise

    def play(self):
        if self.notification_sound:
            self.notification_sound.play()
