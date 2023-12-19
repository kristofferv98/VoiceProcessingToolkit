import contextlib
import os
import struct


import pvporcupine
import pyaudio
import pygame

from VOICEASSISTANT_V5.Agent_setup.Agents import handle_agent_message
from VOICEASSISTANT_V5.Voice_setup.Combined_audio_processing import combined_audio_processing
from VOICEASSISTANT_V5.config.global_config import config

WAKE_WORD = "jarvis"


def get_user_input():
    return input()


notification_path = os.path.join(os.path.dirname(__file__), 'Wav_MP3/notification.wav')


def file_change_detected(file_path, last_modified):
    """
    Checks if the specified file has been modified.

    Args:
        file_path (str): Path to the file to monitor.
        last_modified (list): A single-element list containing the last modification time.

    Returns:
        bool: True if the file has been modified, False otherwise.
    """
    try:
        current_modified = os.path.getmtime(file_path)
        if last_modified[0] is None or current_modified > last_modified[0]:
            last_modified[0] = current_modified
            return True
    except FileNotFoundError:
        pass  # File might not exist yet
    except OSError as e:
        print(f'Error in file change detection: {e}')
    return False


class WakeWordDetector:
    # Suppress pygame's welcome message
    with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f):
        pygame.mixer.init()
    pygame.mixer.init()

    # Load notification sound
    notification_sound = pygame.mixer.Sound(notification_path)
    notification_sound.set_volume(0.3)

    def __init__(self):
        self.access_key = 'b2UbNJ2N5xNROBsICABolmKQwtQN7ARTRTSB+U0lZg+kDieYqcx7nw=='
        self.porcupine = pvporcupine.create(
            access_key=self.access_key,
            keywords=[WAKE_WORD],
            sensitivities=[0.75]
        )

from voice_detection.audio_data_provider import PyAudioDataProvider

        self.audio_data_provider = PyAudioDataProvider(
            rate=self.porcupine.sample_rate,
            channels=1,
            audio_format=pyaudio.paInt16,
            frames_per_buffer=self.porcupine.frame_length
        )

    def init_audio_stream(self):
        # This method might not be necessary anymore if the PyAudioDataProvider handles stream reinitialization internally.

    def typing_loop(self):
        try:
            while True:
                transcription = input("Type your command: ")
                handle_agent_message(transcription)
        except KeyboardInterrupt:
            print('Stopped by user')

    def voice_loop(self):
        try:
            while True:
                try:
                    pcm = self.audio_data_provider.get_audio_frame()
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                    keyword_index = self.porcupine.process(pcm)
                    if keyword_index >= 0:
                        print('Wake word detected!')

                        # Play the notification sound
                        self.notification_sound.play()

                        # Perform audio processing and get transcription
                        transcription = combined_audio_processing()
                        print("-------------------------")
                        print(f'User: {transcription}')
                        if transcription:
                            handle_agent_message(transcription)
                        print('Returning to listening for wake word...')
                except OSError:
                    self.init_audio_stream()  # Reinitialize the audio stream
        except KeyboardInterrupt:
            print('Stopped by user')



    def run(self):
        print("\nWelcome to the Voice Assistant!")
        print("-------------------------------")

        input_mode = config.input_mode

        if input_mode == 'typing':
            print("\nTyping mode activated")
            self.typing_loop()
        elif input_mode == 'voice':
            print("\nVoice mode activated. Listening for the wake word...")
            self.voice_loop()


    def cleanup(self):
        """Release resources."""
        self.audio_data_provider.cleanup()
        self.porcupine.delete()

