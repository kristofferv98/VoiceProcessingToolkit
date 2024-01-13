import threading

shutdown_flag = threading.Event()


class ThreadManager:
    def __init__(self):
        self.threads = []
        self.shutdown_requested = False

    def add_thread(self, thread):
        if thread and isinstance(thread, threading.Thread):
            self.threads.append(thread)

    def join_all(self):
        for thread in self.threads:
            if thread.is_alive():
                try:
                    thread.join()
                except KeyboardInterrupt:
                    # If a KeyboardInterrupt occurs while joining, we set the shutdown flag
                    shutdown_flag.set()
                    # And re-raise the exception to handle it in the outer scope
                    raise

    def shutdown(self):
        shutdown_flag.set()
        self.join_all()
        self.shutdown_requested = True
        # Additional cleanup logic can be added here if necessary

    def handle_keyboard_interrupt(self):
        if not self.shutdown_requested:
            print("KeyboardInterrupt detected, shutting down threads...")
            self.shutdown()


thread_manager = ThreadManager()