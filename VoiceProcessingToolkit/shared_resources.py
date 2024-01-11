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
        # Cleanup WakeWordDetector if it has been initialized
        if hasattr(self, 'wake_word_detector') and self.wake_word_detector:
            self.wake_word_detector.cleanup()
        # Cleanup AudioStreamManager if it has been initialized
        if hasattr(self, 'audio_stream_manager') and self.audio_stream_manager:
            self.audio_stream_manager.cleanup()
        # Close the audio stream if it has been initialized
        if hasattr(self, 'audio_stream_manager') and self.audio_stream_manager:
            self.audio_stream_manager.cleanup()



    def handle_keyboard_interrupt(self):
        if not self.shutdown_requested:
            print("KeyboardInterrupt detected, shutting down threads...")
            self.shutdown()

thread_manager = ThreadManager()
