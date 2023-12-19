import pygame
import os

class NotificationSoundManager:
    def __init__(self, sound_file_path):
        # Suppress pygame's welcome message
        with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
            pygame.mixer.init()
        self.notification_sound = pygame.mixer.Sound(sound_file_path)
        self.notification_sound.set_volume(0.3)

    def play_notification(self):
        self.notification_sound.play()
