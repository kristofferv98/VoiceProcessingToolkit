import logging
import pyaudio

logger = logging.getLogger(__name__)


class AudioStream:
    def __init__(self, rate: int, channels: int, _audio_format: int, frames_per_buffer: int):
        self._py_audio = pyaudio.PyAudio()
        self._stream = self._initialize_stream(rate, channels, _audio_format, frames_per_buffer)

    def _initialize_stream(self, rate: int, channels: int, _audio_format: int, frames_per_buffer: int):
        """
        Initializes the audio stream with the given parameters.
        """
        try:
            return self._py_audio.open(rate=rate, channels=channels, format=_audio_format,
                                       input=True, frames_per_buffer=frames_per_buffer)
        except pyaudio.PyAudio as e:
            logger.exception("Failed to initialize audio stream: %s", e)
            raise
        except Exception as e:
            logger.exception("An unexpected error occurred while initializing the audio stream.", exc_info=e)
            raise

    def get_stream(self):
        """Returns the initialized audio stream."""
        return self._stream

class AudioStream:
    ...
    def cleanup(self):
        """Cleans up the audio stream and terminates the PyAudio instance."""
        if self._stream and self._stream.is_active():
            self._stream.stop_stream()
        self._stream.close()
        self._py_audio.terminate()
