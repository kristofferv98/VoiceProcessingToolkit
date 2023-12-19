import logging
import pyaudio

logger = logging.getLogger(__name__)

class AudioStreamManager:
    def __init__(self, rate: int, channels: int, format: int, frames_per_buffer: int):
        self.py_audio = pyaudio.PyAudio()
        self.stream = self._initialize_stream(rate, channels, format, frames_per_buffer)

    def _initialize_stream(self, rate: int, channels: int, format: int, frames_per_buffer: int):
        try:
            return self.py_audio.open(rate=rate, channels=channels, format=format,
                                      input=True, frames_per_buffer=frames_per_buffer)
        except pyaudio.PyAudioError as e:
            logger.exception("Failed to initialize audio stream due to PyAudio error.", exc_info=e)
            raise
        except Exception as e:
            logger.exception("An unexpected error occurred while initializing the audio stream.", exc_info=e)
            raise

    def get_stream(self):
        return self.stream

    def cleanup(self):
        if self.stream.is_active():
            self.stream.stop_stream()
        self.stream.close()
        self.py_audio.terminate()
