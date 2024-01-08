import logging
import os
import threading

import pyaudio
from dotenv import load_dotenv

from VoiceProcessingToolkit.transcription.whisper import WhisperTranscriber
from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector, AudioStream
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager, register_action_decorator

from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
logger = logging.getLogger(__name__)


class VoiceProcessingManager:
    def __init__(self, wake_word='jarvis', sensitivity=0.5, output_directory='Wav_MP3',
                 audio_format=pyaudio.paInt16, channels=1, rate=16000, frames_per_buffer=512,
                 voice_threshold=0.8, silence_limit=2, inactivity_limit=2, min_recording_length=3, buffer_length=2):
        self.wake_word = wake_word
        self.sensitivity = sensitivity
        self.output_directory = output_directory
        self.audio_format = audio_format
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.voice_threshold = voice_threshold
        self.silence_limit = silence_limit
        self.inactivity_limit = inactivity_limit
        self.min_recording_length = min_recording_length
        self.buffer_length = buffer_length
        self.audio_stream_manager = None
        self.wake_word_detector = None
        self.voice_recorder = None
        self.transcriber = WhisperTranscriber()
        self.action_manager = ActionManager()
        self.setup()
        self.recording_thread = None

    def setup(self):
        # Initialize AudioStream
        self.audio_stream_manager = AudioStream(rate=self.rate, channels=self.channels,
                                                _audio_format=self.audio_format, frames_per_buffer=self.frames_per_buffer)

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
        self.voice_recorder = AudioRecorder(output_directory=self.output_directory, audio_format=self.audio_format,
                                            channels=self.channels, rate=self.rate, frames_per_buffer=self.frames_per_buffer,
                                            voice_threshold=self.voice_threshold, silence_limit=self.silence_limit,
                                            inactivity_limit=self.inactivity_limit, min_recording_length=self.min_recording_length,
                                            buffer_length=self.buffer_length)
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
                recorded_file = self.voice_recorder.last_saved_file
                if recorded_file:
                    # Transcribe the recorded audio
                    transcription = self.transcriber.transcribe_audio(recorded_file)
                    if transcription:
                        logger.info(f"Transcription: {transcription}")
                if recorded_file:
                    logger.info(f"Voice recording saved to {recorded_file}")
            else:
                logger.warning("A recording is already in progress.")

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
