import logging
import pyaudio

logger = logging.getLogger(__name__)


class AudioStream:
    def __init__(self, rate: int, channels: int, _audio_format: int, frames_per_buffer: int):
        self._py_audio = pyaudio.PyAudio()
        self._frames_per_buffer = frames_per_buffer
        self._pre_buffer_seconds = 1.5  # Duration to keep before wake word
        self._post_buffer_seconds = 1.5  # Duration to keep after wake word
        # Calculate the buffer size based on the duration and sample rate
        self._buffer_size = int(rate * self._frames_per_buffer * (self._pre_buffer_seconds + self._post_buffer_seconds))
        self._rolling_buffer = bytearray(self._buffer_size)
        self._stream = self._initialize_stream(rate, channels, _audio_format, frames_per_buffer)


    def update_rolling_buffer(self, data: bytes) -> None:
        """
        Updates the rolling buffer with new audio data.

        Args:
            data (bytes): The audio data to add to the rolling buffer.
        """
        # Append new data to the end of the rolling buffer
        self._rolling_buffer += data
        # Remove the oldest data to maintain the buffer size
        self._rolling_buffer = self._rolling_buffer[-self._buffer_size:]

    def get_rolling_buffer(self) -> bytes:
        """
        Retrieves the current rolling buffer audio data.

        Returns:
            bytes: The current audio data in the rolling buffer.
        """
        return bytes(self._rolling_buffer)

    def is_stream_closed(self):
        """
        Checks if the audio stream is closed.

        Returns:
            bool: True if the stream is closed, False otherwise.
        """
        return self._stream is None or self._stream.is_stopped()

    def _initialize_stream(self, rate: int, channels: int, _audio_format: int, frames_per_buffer: int):
        """
        Initializes the audio stream with the given parameters.
        """
        try:
            self._stream = self._py_audio.open(rate=rate, channels=channels, format=_audio_format,
                                               input=True, frames_per_buffer=frames_per_buffer)
            return self._stream
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
        data = bytearray()
        try:
            data.extend(self._stream.read(self._frames_per_buffer, exception_on_overflow=False))
        except IOError as e:
            # Handle input overflow error if it occurs
            if e.errno == pyaudio.paInputOverflowed:
                logger.warning("Input overflow occurred while reading audio stream.")
            else:
                raise

        # Update the rolling buffer with the new data
        self.update_rolling_buffer(bytes(data))
        return data

    def cleanup(self):
        """Cleans up the audio stream and terminates the PyAudio instance."""
        try:
            if self._stream and not self._stream.is_stopped():
                self._stream.stop_stream()
            if self._stream:
                self._stream.close()
        finally:
            self._py_audio.terminate()
            self._stream = None
