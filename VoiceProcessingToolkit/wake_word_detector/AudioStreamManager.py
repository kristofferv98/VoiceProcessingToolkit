import logging
import pyaudio

logger = logging.getLogger(__name__)


class AudioStream:
    def __init__(self, rate: int, channels: int, audio_format: int, frames_per_buffer: int):
        self.py_audio = pyaudio.PyAudio()
        self.stream = self._initialize_stream(rate, channels, audio_format, frames_per_buffer)

    def _initialize_stream(self, rate: int, channels: int, audio_format: int, frames_per_buffer: int):
        try:
            return self.py_audio.open(rate=rate, channels=channels, format=audio_format,
                                      input=True, frames_per_buffer=frames_per_buffer)
        except pyaudio.PyAudio as e:
            logger.exception("Failed to initialize audio stream: %s", e)
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
