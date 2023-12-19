import pyaudio
import numpy as np
from abc import ABC, abstractmethod


class AudioDataProvider(ABC):
    @abstractmethod
    def get_audio_frame(self):
        """Returns a single frame of audio data."""
        pass

    @abstractmethod
    def cleanup(self):
        """Cleans up any resources used by the provider."""
        pass


class PyAudioDataProvider(AudioDataProvider):
    def __init__(self, rate=16000, channels=1, audio_format=pyaudio.paInt16, frames_per_buffer=1024):
        self.rate = rate
        self.channels = channels
        self.audio_format = audio_format
        self.frames_per_buffer = frames_per_buffer
        self.py_audio = pyaudio.PyAudio()
        self.stream = None
        self.open_stream()

    def open_stream(self):
        """Opens the audio stream with the specified parameters."""
        try:
            self.stream = self.py_audio.open(
                rate=self.rate,
                channels=self.channels,
                format=self.audio_format,
                input=True,
                frames_per_buffer=self.frames_per_buffer
            )
        except pyaudio.PyAudio as e:
            print(f"Could not open audio stream: {e}")
            self.cleanup()

    def get_audio_frame(self):
        """Returns a single frame of audio data from the stream."""
        if not self.stream:
            raise IOError("Audio stream is not open")

        try:
            # Check if there is enough data to read to prevent overflow/underflow
            if self.stream.get_read_available() >= self.frames_per_buffer:
                frame = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
                return np.frombuffer(frame, dtype=np.int16)
        except IOError as e:
            print(f"Error reading audio frame: {e}")
        return None

    def cleanup(self):
        """Cleans up the audio stream and PyAudio instance."""
        if self.stream and not self.stream.is_stopped():
            self.stream.stop_stream()
        if self.stream and not self.stream.is_closed():
            self.stream.close()
        self.py_audio.terminate()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
