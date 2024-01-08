import logging
import os
import threading

import pyaudio
from dotenv import load_dotenv

from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector, AudioStream
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager, register_action_decorator

logger = logging.getLogger(__name__)


class VoiceProcessingManager:
    def __init__(self, wake_word='jarvis', sensitivity=0.5, output_directory='Wav_MP3'):
        self.wake_word = wake_word
        self.sensitivity = sensitivity
        self.output_directory = output_directory
        self.audio_stream_manager = None
        self.wake_word_detector = None
        self.voice_recorder = None
        self.action_manager = ActionManager()
        self.setup()
        self.recording_thread = None

    def setup(self):
        # Initialize AudioStream
        self.audio_stream_manager = AudioStream(rate=16000, channels=1, _audio_format=pyaudio.paInt16,
                                                frames_per_buffer=512)

        # Initialize WakeWordDetector
        self.wake_word_detector = WakeWordDetector(
            access_key=os.environ.get('PICOVOICE_APIKEY') or os.getenv('PICOVOICE_APIKEY'),
            wake_word=self.wake_word,
            sensitivity=self.sensitivity,
            action_manager=self.action_manager,
            audio_stream_manager=self.audio_stream_manager,
            play_notification_sound=True
        )
        # Initialize VoiceRecorder
        self.voice_recorder = AudioRecorder(output_directory=self.output_directory)
        # Register the voice recording action
        self.register_voice_recording_action()

    def register_voice_recording_action(self):
        @register_action_decorator(self.action_manager)
        def start_voice_recording():
            logger.info("Wake word detected, starting voice recording...")
            # Start the recording in a separate thread to avoid blocking the main thread
            if self.recording_thread is None or not self.recording_thread.is_alive():
                self.recording_thread = threading.Thread(target=self.voice_recorder.perform_recording)
                self.recording_thread.start()
                self.recording_thread.join()  # Wait for the recording to finish
                recorded_file = self.voice_recorder.get_last_saved_file()  # Retrieve the path of the last saved file
                if recorded_file:
                    logger.info(f"Voice recording saved to {recorded_file}")
            else:
                logger.warning("A recording is already in progress.")

    def get_last_saved_file(self):
        """
        Retrieves the path of the last saved audio file from the voice recorder.
        Returns:
            str: The path to the last saved audio file.
        """
        return self.voice_recorder.get_last_saved_file()

    def run(self):
        try:
            self.wake_word_detector.run()
        except KeyboardInterrupt:
            logger.info("Voice processing stopped by user.")
        except Exception as e:
            logger.exception("An error occurred during voice processing.", exc_info=e)
        finally:
            self.cleanup()

    def cleanup(self):
        self.audio_stream_manager.cleanup()
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join()
        self.voice_recorder.cleanup()


if __name__ == '__main__':
    load_dotenv()
    # set the
    logging.basicConfig(level=logging.INFO)
    manager = VoiceProcessingManager()
    manager.run()
