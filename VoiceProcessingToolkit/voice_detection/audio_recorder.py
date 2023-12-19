import logging
import wave
import os
from collections import deque
from .cobra import PyAudioDataProvider
from .voice_activity_detector import VoiceActivityDetector

class AudioRecorder:
    def __init__(self, access_key, audio_data_provider=None):
        # Configuration attributes from sample code
        self.VOICE_THRESHOLD = 0.8
        self.SILENCE_LIMIT = 2
        self.BUFFER_LENGTH = 2
        self.INACTIVITY_LIMIT = 2
        self.MIN_RECORDING_LENGTH = 3

        self.voice_activity_detector = VoiceActivityDetector(access_key)
        self.audio_data_provider = audio_data_provider or PyAudioDataProvider(rate=self.voice_activity_detector.sample_rate, frames_per_buffer=self.voice_activity_detector.frame_length)
        self.frames_to_save = deque(maxlen=self.BUFFER_LENGTH * self.voice_activity_detector.sample_rate // self.voice_activity_detector.frame_length)
        self.is_recording = False

    def start_recording(self):
        # Logic to start recording using voice_activity_detector and audio_data_provider from sample code
        # ... (Implement the logic from the sample code's start_recording method here) ...

    def save_to_wav_file(self, frames):
        # Logic to save frames to a WAV file from sample code
        # ... (Implement the logic from the sample code's save_to_wav_file method here) ...

    def cleanup(self):
        self.voice_activity_detector.cleanup()
        self.audio_data_provider.cleanup()
