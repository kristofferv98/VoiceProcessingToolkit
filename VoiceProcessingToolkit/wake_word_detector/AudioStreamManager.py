import logging
import pyaudio

logger = logging.getLogger(__name__)


class AudioStream:
    def __init__(self, rate: int, channels: int, _audio_format: int, frames_per_buffer: int):
        self._py_audio = pyaudio.PyAudio()
        self._buffer_size = 10 * frames_per_buffer  # Adjust the buffer size as needed
        self._rolling_buffer = bytearray(self._buffer_size)
        self._stream = self._initialize_stream(rate, channels, _audio_format, frames_per_buffer)

    def update_rolling_buffer(self, data: bytes) -> None:
        """
        Updates the rolling buffer with new audio data.

        Args:
            data (bytes): The audio data to add to the rolling buffer.
        """
        self._rolling_buffer = (self._rolling_buffer + data)[-self._buffer_size:]

    def get_rolling_buffer(self) -> bytes:
        """
        Retrieves the current rolling buffer audio data.

        Returns:
            bytes: The current audio data in the rolling buffer.
        """
        return bytes(self._rolling_buffer)

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


    def read(self) -> bytes:
        """
        Reads audio data from the stream and updates the rolling buffer.

        Returns:
            bytes: The audio data read from the stream.
        """
        data = self._stream.read(self._stream.get_read_available(), exception_on_overflow=False)
        self.update_rolling_buffer(data)
        return data

    def cleanup(self):
        """Cleans up the audio stream and terminates the PyAudio instance."""
        if self._stream and not self._stream.is_stopped():
            self._stream.stop_stream()
        self._stream.close()
        self._py_audio.terminate()
