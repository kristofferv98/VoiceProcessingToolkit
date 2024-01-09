import logging
import os
import threading

import pyaudio
import pygame
from dotenv import load_dotenv

from VoiceProcessingToolkit.transcription.whisper import WhisperTranscriber
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector, AudioStream
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager, register_action_decorator
from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
from text_to_speech.elevenlabs_tts import text_to_speech_stream, text_to_speech

logger = logging.getLogger(__name__)


class VoiceProcessingManager:
    def __init__(self, wake_word='jarvis', sensitivity=0.5, output_directory='Wav_MP3',
                 audio_format=pyaudio.paInt16, channels=1, rate=16000, frames_per_buffer=512,
                 voice_threshold=0.8, silence_limit=2, inactivity_limit=2, min_recording_length=3, buffer_length=2):
        """
        Manages the voice processing workflow including wake word detection, voice recording, and transcription.

    class VoiceProcessingManager:
        def __init__(self, wake_word='jarvis', sensitivity=0.5, output_directory='Wav_MP3',
                     audio_format=pyaudio.paInt16, channels=1, rate=16000, frames_per_buffer=512,
                     voice_threshold=0.8, silence_limit=2, inactivity_limit=2, min_recording_length=3, buffer_length=2):
        Initializes the VoiceProcessingManager with the provided parameters.

        Args:
            wake_word (str): The wake word to activate voice recording.
            sensitivity (float): The sensitivity of the wake word detection.
            output_directory (str): The directory where recordings will be saved.
            audio_format (int): The format of the audio stream.
            channels (int): The number of audio channels.
            rate (int): The sample rate of the audio stream.
            frames_per_buffer (int): The number of frames per buffer.
            voice_threshold (float): The threshold for voice detection.
            silence_limit (int): The number of seconds of silence before stopping the recording.
            inactivity_limit (int): The number of seconds of inactivity before stopping the recording.
            min_recording_length (int): The minimum length of a valid recording.
            buffer_length (int): The length of the audio buffer.
        """
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

    def start_voice_processing(self):
        """
        Starts the entire voice processing workflow including wake word detection, recording, and transcription.
        """
        try:
            self.start_detector()
            transcription = self.voice_recorder.transcribe_last_recording()
            if transcription:
                logger.info(f"Transcription: {transcription}")
                text_to_speech(transcription)
        except Exception as e:
            logger.exception("An error occurred during voice processing.", exc_info=e)
        finally:
            self.cleanup()

    def start_detector(self):
        """
        Starts the wake word detection.
        """
        try:
            self.wake_word_detector.run()
        except Exception as e:
            logger.exception("An error occurred during voice processing.", exc_info=e)


    def setup(self):
        # Initialize AudioStream
        self.audio_stream_manager = AudioStream(rate=self.rate, channels=self.channels,
                                                _audio_format=self.audio_format,
                                                frames_per_buffer=self.frames_per_buffer)

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
        self.voice_recorder = AudioRecorder(output_directory=self.output_directory,
                                            voice_threshold=self.voice_threshold,
                                            silence_limit=self.silence_limit, inactivity_limit=self.inactivity_limit,
                                            min_recording_length=self.min_recording_length,
                                            buffer_length=self.buffer_length)

    def cleanup(self):
        """
        Cleans up the resources used by the voice processing manager.
        """
        self.audio_stream_manager.cleanup()
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join()
            self.voice_recorder.cleanup()


        if self.wake_word_detector:
            self.wake_word_detector.cleanup()
        if self.transcriber:
            self.transcriber.cleanup()

    def transcribe_last_recording(self):
        """
        Transcribes the last recorded audio file.
        """
        if self.voice_recorder.last_saved_file:
            return self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
        return None

if __name__ == '__main__':
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    voice_processing_manager = VoiceProcessingManager()
    voice_processing_manager.start_voice_processing()
