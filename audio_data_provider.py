# === IMPLEMENTATION OF AUDIO DATA PROVIDER INTERFACE ===

import pyaudio
import numpy as np

class PyAudioDataProvider(AudioDataProvider):
    """
    PyAudioDataProvider provides audio data frames using PyAudio.
    """

    def __init__(self, stream):
        """
        Initialize the PyAudioDataProvider with an audio stream.
        Args:
            stream: An instance of PyAudio stream to read audio data from.
        """
        self.stream = stream

    def get_audio_frame(self):
        """
        Returns a single frame of audio data from the stream.
        """
        frame = self.stream.read(self.stream.get_read_available(), exception_on_overflow=False)
        return np.frombuffer(frame, dtype=np.int16)
