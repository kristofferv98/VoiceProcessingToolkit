import logging
import wave
import os
from collections import deque
from .voice_activity_detector import VoiceActivityDetector
from .audio_data_provider import PyAudioDataProvider

class AudioRecorder:
    def __init__(self, access_key, audio_data_provider=None):
        self.voice_activity_detector = VoiceActivityDetector(access_key)
        self.audio_data_provider = audio_data_provider or PyAudioDataProvider()
        self.frames_to_save = deque()
        self.is_recording = False
        # ... other configuration attributes ...

    def start_recording(self):
        # ... logic to start recording using voice_activity_detector and audio_data_provider ...

    def save_to_wav_file(self, frames):
        # ... logic to save frames to a WAV file ...

    def cleanup(self):
        self.voice_activity_detector.cleanup()
        self.audio_data_provider.cleanup()
