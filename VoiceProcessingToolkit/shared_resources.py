import logging
import threading
import traceback
from typing import List, Dict, Optional, Callable, Any

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
