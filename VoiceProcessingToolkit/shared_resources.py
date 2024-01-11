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
                thread.join()

    def shutdown(self):
        shutdown_flag.set()
        self.join_all()
        self.shutdown_requested = True



    def handle_keyboard_interrupt(self):
        if not self.shutdown_requested:
            print("KeyboardInterrupt detected, shutting down threads...")
            self.shutdown()

thread_manager = ThreadManager()
