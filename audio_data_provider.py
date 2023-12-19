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
import pyaudio
import numpy as np

class PyAudioDataProvider:
    """
    PyAudioDataProvider provides audio data frames using PyAudio.
    """

    def __init__(self, rate, channels, format, frames_per_buffer):
        """
        Initialize the PyAudioDataProvider with audio stream parameters.
        Args:
            rate: The sample rate.
            channels: The number of audio channels.
            format: The sample format.
            frames_per_buffer: The number of frames per buffer.
        """
        self.py_audio = pyaudio.PyAudio()
        self.stream = self.py_audio.open(
            rate=rate,
            channels=channels,
            format=format,
            frames_per_buffer=frames_per_buffer,
            input=True
        )

    def get_audio_frame(self):
        """
        Returns a single frame of audio data from the stream.
        """
        frame = self.stream.read(self.stream.get_read_available(), exception_on_overflow=False)
        return np.frombuffer(frame, dtype=np.int16)

    def cleanup(self):
        """
        Clean up the audio stream and PyAudio instance.
        """
        self.stream.stop_stream()
        self.stream.close()
        self.py_audio.terminate()
