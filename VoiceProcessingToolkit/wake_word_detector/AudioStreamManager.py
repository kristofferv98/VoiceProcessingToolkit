import logging
import pyaudio
import threading
import wave
from typing import Optional, Dict, Any

from VoiceProcessingToolkit.interfaces import AudioStreamInterface
from VoiceProcessingToolkit.shared_resources import thread_manager

class AudioStream(AudioStreamInterface):
    """
    Manages audio input streams and maintains a rolling buffer of audio data.
    Implements the AudioStreamInterface.
    
    Attributes:
        rolling_buffer_size (int): Size of the rolling buffer in bytes.
        rolling_buffer (bytes): Buffer holding the most recent audio data.
        p (pyaudio.PyAudio): PyAudio instance.
        stream (pyaudio.Stream): Audio input stream.
        is_closed (bool): Flag indicating if the stream is closed.
        logger (logging.Logger): Logger for this class.
        _lock (threading.Lock): Lock for thread-safe operations on the rolling buffer.
    """
    
    def __init__(self, rolling_buffer_size: int = 8000):
        """
        Initialize a new AudioStream instance.
        
        Args:
            rolling_buffer_size: Size of the rolling buffer in bytes (default: 8000).
        """
        self.rolling_buffer_size = rolling_buffer_size
        self.rolling_buffer = b''
        self.p: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.is_closed = True
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
    
    def initialize_stream(self, rate: int, channels: int, audio_format: int, frames_per_buffer: int) -> None:
        """
        Initialize the audio stream with the given parameters.
        
        Args:
            rate: Sample rate of the audio stream.
            channels: Number of audio channels.
            audio_format: Format of the audio stream.
            frames_per_buffer: Number of audio frames per buffer.
        
        Raises:
            RuntimeError: If PyAudio initialization or stream opening fails.
        """
        # Clean up any existing resources first
        self.cleanup()
        
        try:
            self.p = pyaudio.PyAudio()
            self.stream = self.p.open(
                format=audio_format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=frames_per_buffer
            )
            self.is_closed = False
            self.logger.info("Audio stream initialized successfully")
        except Exception as e:
            self.cleanup()  # Clean up partial resources on failure
            self.logger.error(f"Failed to initialize audio stream: {e}")
            raise RuntimeError(f"Failed to initialize audio stream: {e}")
    
    def read(self) -> bytes:
        """
        Read audio data from the stream.
        
        Returns:
            bytes: The audio data read from the stream.
            
        Raises:
            RuntimeError: If the stream is closed or an error occurs while reading.
        """
        if self.is_stream_closed():
            self.logger.error("Attempted to read from closed stream")
            raise RuntimeError("Cannot read from closed audio stream")
        
        try:
            data = self.stream.read(1024, exception_on_overflow=False)
            return data
        except Exception as e:
            self.logger.error(f"Error reading from audio stream: {e}")
            raise RuntimeError(f"Error reading from audio stream: {e}")
    
    def get_stream(self) -> Optional[pyaudio.Stream]:
        """
        Get the underlying audio stream.
        
        Returns:
            Optional[pyaudio.Stream]: The audio stream object or None if not initialized.
        """
        return self.stream
    
    def is_stream_closed(self) -> bool:
        """
        Check if the audio stream is closed.
        
        Returns:
            bool: True if the stream is closed, False otherwise.
        """
        return self.is_closed or self.stream is None
    
    def cleanup(self) -> None:
        """
        Clean up resources used by the audio stream.
        Safe to call multiple times.
        """
        with self._lock:
            # Mark as closed first to prevent new operations
            self.is_closed = True
            
            # Stop and close the stream
            if self.stream is not None:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                    self.logger.debug("Audio stream closed")
                except Exception as e:
                    self.logger.warning(f"Error closing audio stream: {e}")
                finally:
                    self.stream = None
            
            # Terminate PyAudio
            if self.p is not None:
                try:
                    self.p.terminate()
                    self.logger.debug("PyAudio terminated")
                except Exception as e:
                    self.logger.warning(f"Error terminating PyAudio: {e}")
                finally:
                    self.p = None
    
    def update_rolling_buffer(self, data: bytes) -> None:
        """
        Update the rolling buffer with new audio data.
        Thread-safe implementation.
        
        Args:
            data: The audio data to add to the rolling buffer.
        """
        with self._lock:
            # Append the new data to the rolling buffer
            self.rolling_buffer += data
            
            # Trim the buffer if it exceeds the maximum size
            if len(self.rolling_buffer) > self.rolling_buffer_size:
                self.rolling_buffer = self.rolling_buffer[-self.rolling_buffer_size:]
    
    def get_rolling_buffer(self) -> bytes:
        """
        Get the current rolling buffer audio data.
        Thread-safe implementation.
        
        Returns:
            bytes: The current audio data in the rolling buffer.
        """
        with self._lock:
            return self.rolling_buffer
    
    def __del__(self):
        """Ensure cleanup when the object is garbage collected."""
        self.cleanup()

