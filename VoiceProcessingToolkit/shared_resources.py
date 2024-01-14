import logging
import threading

shutdown_flag = threading.Event()

logger = logging.getLogger(__name__)

class ThreadManager:
    def __init__(self):
        self.threads = []
        self.shutdown_requested = False

    def add_thread(self, thread):
        if thread and isinstance(thread, threading.Thread):
            logger.info("Adding thread %s to thread manager", thread.name)
            self.threads.append(thread)

    def join_all(self):
        for thread in self.threads:
            logger.info("Joining thread %s", thread.name)
            if thread.is_alive():
                logger.info("Thread %s is alive, joining...", thread.name)
                try:
                    thread.join()
                except KeyboardInterrupt:
                    # If a KeyboardInterrupt occurs while joining, we set the shutdown flag
                    shutdown_flag.set()
                    # And re-raise the exception to handle it in the outer scope
                    raise

    def shutdown(self):
        # Ensure that shutdown is only performed once
        logger.info("Shutdown requested")
        if self.shutdown_requested:
            return
        shutdown_flag.set()
        # Signal all threads to shutdown
        shutdown_flag.set()
        self.join_all()
        self.shutdown_requested = True
        # Additional cleanup logic can be added here if necessary
        # Clean up the threads list
        self.threads = []
        shutdown_flag.clear()

    def handle_keyboard_interrupt(self):
        if not self.shutdown_requested:
            logger.info("KeyboardInterrupt detected, shutting down threads...")
            self.shutdown()


thread_manager = ThreadManager()
