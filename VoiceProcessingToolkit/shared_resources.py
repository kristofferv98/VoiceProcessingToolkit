import logging
import threading
import traceback
from typing import List, Dict, Optional, Callable, Any
import pyaudio

shutdown_flag = threading.Event()

logger = logging.getLogger(__name__)

class ThreadManager:
    """
    Manages multiple threads, providing methods for adding threads,
    joining all threads, and handling shutdown requests.
    
    Attributes:
        threads (List[threading.Thread]): List of threads managed by this instance.
        shutdown_requested (threading.Event): Event used to signal shutdown request.
        logger (logging.Logger): Logger for this class.
        thread_errors (Dict[str, Exception]): Dictionary mapping thread names to exceptions that occurred in them.
        _lock (threading.Lock): Lock for thread-safe operations on shared data.
    """
    
    def __init__(self):
        """Initialize a new ThreadManager instance."""
        self.threads: List[threading.Thread] = []
        self.shutdown_requested = threading.Event()
        self.logger = logging.getLogger(__name__)
        self.thread_errors: Dict[str, Exception] = {}
        self._lock = threading.Lock()
    
    def add_thread(self, thread: threading.Thread) -> None:
        """
        Add a thread to be managed.
        
        Args:
            thread (threading.Thread): The thread to add.
        """
        with self._lock:
            if thread not in self.threads:
                self.threads.append(thread)
                self.logger.debug(f"Added thread: {thread.name}")
    
    def join_all_threads(self, timeout: Optional[float] = None) -> bool:
        """
        Join all threads with an optional timeout.
        
        Args:
            timeout (float, optional): The maximum time to wait for each thread to join.
                                       If None, wait indefinitely.
        
        Returns:
            bool: True if all threads were joined successfully, False otherwise.
        """
        all_joined = True
        threads_to_join = []
        
        # Make a copy of the threads list to avoid modification during iteration
        with self._lock:
            threads_to_join = self.threads.copy()
        
        for thread in threads_to_join:
            if thread.is_alive():
                self.logger.debug(f"Joining thread: {thread.name}")
                thread.join(timeout)
                if thread.is_alive():
                    self.logger.warning(f"Thread {thread.name} did not join within the timeout")
                    all_joined = False
            
            # Remove joined threads from our list
            with self._lock:
                if thread in self.threads and not thread.is_alive():
                    self.threads.remove(thread)
        
        return all_joined
    
    def shutdown(self) -> None:
        """
        Signal all threads to shut down and clean up.
        This ensures that shutdown is performed only once.
        """
        if not self.shutdown_requested.is_set():
            self.logger.info("Shutdown requested")
            self.shutdown_requested.set()
            
            # Join threads with a timeout to avoid hanging
            if not self.join_all_threads(timeout=5.0):
                self.logger.warning("Some threads did not shut down gracefully within the timeout")
            
            # Report any thread errors
            if self.thread_errors:
                self.logger.error(f"Errors occurred in {len(self.thread_errors)} threads:")
                for thread_name, error in self.thread_errors.items():
                    self.logger.error(f"Error in thread {thread_name}: {error}")
            
            with self._lock:
                self.threads.clear()
    
    def handle_keyboard_interrupt(self) -> None:
        """Handle keyboard interrupt by requesting shutdown."""
        self.logger.info("Keyboard interrupt detected")
        self.shutdown()
    
    def create_daemon_thread(self, target: Callable, name: str, args: tuple = (), kwargs: dict = None) -> threading.Thread:
        """
        Create and register a daemon thread.
        
        Args:
            target (Callable): The function to run in the thread.
            name (str): Name for the thread.
            args (tuple): Arguments for the target function.
            kwargs (dict, optional): Keyword arguments for the target function.
        
        Returns:
            threading.Thread: The created thread.
        """
        if kwargs is None:
            kwargs = {}
        
        # Wrap the target function to catch and log exceptions
        def wrapped_target(*args, **kwargs):
            try:
                return target(*args, **kwargs)
            except Exception as e:
                with self._lock:
                    self.thread_errors[threading.current_thread().name] = e
                self.logger.error(f"Exception in thread {threading.current_thread().name}: {e}")
                self.logger.error(traceback.format_exc())
                # Signal shutdown if a thread crashes
                self.shutdown_requested.set()
        
        thread = threading.Thread(target=wrapped_target, name=name, args=args, kwargs=kwargs)
        thread.daemon = True
        self.add_thread(thread)
        return thread
    
    def is_shutdown_requested(self) -> bool:
        """
        Check if shutdown has been requested.
        
        Returns:
            bool: True if shutdown has been requested, False otherwise.
        """
        return self.shutdown_requested.is_set()
    
    def wait_for_shutdown_request(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for a shutdown request.
        
        Args:
            timeout (float, optional): The maximum time to wait. If None, wait indefinitely.
        
        Returns:
            bool: True if shutdown was requested, False if timeout occurred.
        """
        return self.shutdown_requested.wait(timeout)


# Create a global instance
thread_manager = ThreadManager()
shutdown_flag = thread_manager.shutdown_requested

class AudioDataProvider:
    """
    Provides audio data from the microphone.
    This class manages a PyAudio stream and provides convenient methods for reading audio data.
    """
    def __init__(
        self,
        rate: int = 16000,
        channels: int = 1,
        audio_format: int = pyaudio.paInt16,
        frames_per_buffer: int = 512
    ):
        """
        Initialize a new AudioDataProvider.
        
        Args:
            rate: Sample rate for audio recording (Hz)
            channels: Number of audio channels
            audio_format: PyAudio format (e.g. pyaudio.paInt16)
            frames_per_buffer: Number of frames per buffer
        """
        self.rate = rate
        self.channels = channels
        self.audio_format = audio_format
        self.frames_per_buffer = frames_per_buffer
        
        # Initialize PyAudio
        self._pyaudio = pyaudio.PyAudio()
        self._stream = None
        self._is_streaming = False
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.debug(f"AudioDataProvider initialized: rate={rate}, channels={channels}, format={audio_format}")
    
    def start_stream(self) -> bool:
        """
        Start the audio stream.
        
        Returns:
            bool: True if the stream was started successfully, False otherwise
        """
        with self._lock:
            if self._is_streaming:
                logger.debug("Stream is already running")
                return True
            
            try:
                self._stream = self._pyaudio.open(
                    format=self.audio_format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.frames_per_buffer
                )
                self._is_streaming = True
                logger.debug("Audio stream started successfully")
                return True
            except Exception as e:
                logger.error(f"Error starting audio stream: {e}")
                return False
    
    def read_audio(self, exception_on_overflow=False) -> Optional[bytes]:
        """
        Read audio data from the stream.
        
        Args:
            exception_on_overflow: Whether to raise an exception on buffer overflow
            
        Returns:
            bytes or None: Audio data if read successfully, None if the stream is not active
        """
        with self._lock:
            if not self._is_streaming or self._stream is None:
                return None
            
            try:
                data = self._stream.read(self.frames_per_buffer, exception_on_overflow)
                return data
            except Exception as e:
                logger.error(f"Error reading audio data: {e}")
                return None
    
    def stop_stream(self) -> None:
        """
        Stop the audio stream and release resources.
        """
        with self._lock:
            if self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except Exception as e:
                    logger.error(f"Error stopping audio stream: {e}")
                finally:
                    self._stream = None
                    self._is_streaming = False
    
    def get_sample_size(self) -> int:
        """
        Get the sample size in bytes for the current audio format.
        
        Returns:
            int: Sample size in bytes
        """
        return self._pyaudio.get_sample_size(self.audio_format)
    
    def cleanup(self) -> None:
        """
        Clean up all resources used by the audio provider.
        """
        self.stop_stream()
        if self._pyaudio:
            self._pyaudio.terminate()
            self._pyaudio = None
    
    def __del__(self) -> None:
        """
        Ensure resources are properly cleaned up when the object is garbage collected.
        """
        self.cleanup()
