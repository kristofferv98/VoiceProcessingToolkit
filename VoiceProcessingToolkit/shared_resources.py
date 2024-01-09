import threading

shutdown_flag = threading.Event()

class ThreadManager:
    def __init__(self):
        self.threads = []

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

thread_manager = ThreadManager()
