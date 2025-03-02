import logging
import os
import threading
import time

import pyaudio

from VoiceProcessingToolkit.transcription.elevenlabs import ElevenLabsTranscriber
from VoiceProcessingToolkit.wake_word_detector.AudioStreamManager import AudioStream
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager
from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
from VoiceProcessingToolkit.shared_resources import thread_manager

logger = logging.getLogger(__name__)

class VoiceProcessingManager:
    def __init__(self, transcriber, action_manager, audio_stream_manager, wake_word='computer', sensitivity=0.75,
                 output_directory='Wav_MP3', wake_word_output='wake_word_output',
                 audio_format=pyaudio.paInt16, channels=1, rate=16000, frames_per_buffer=512,
                 voice_threshold=0.8, silence_limit=2.0, inactivity_limit=2.0, min_recording_length=2.0, buffer_length=2.0,
                 use_wake_word=True, save_wake_word_recordings=False, play_notification_sound=True):
        """
        Manages the voice processing pipeline, including optional wake word detection, voice recording, and transcription.
        It can be configured to handle different use cases:
        - Wake Word Detection: When enabled, the manager listens for a specific wake word before activating recording.
        - Transcription Only: Records and transcribes speech without wake word detection.
        - Notification Sound: Plays a notification sound when the wake word is detected, if enabled.


        Manages the voice processing pipeline, including wake word detection, voice recording, and transcription.

        This class integrates different components such as wake word detection, voice recording, and speech
        transcription. It provides a high-level interface to manage the flow of processing voice commands.


        Attributes:
            wake_word (str): Wake word for triggering voice recording.
            sensitivity (float): Sensitivity for wake word detection.
            output_directory (str): Directory for saving recorded audio files.
            audio_format (int): Format of the audio stream (e.g., pyaudio.paInt16).
            channels (int): Number of audio channels.
            rate (int): Sample rate of the audio stream.
            frames_per_buffer (int): Number of audio frames per buffer.
            voice_threshold (float): Threshold for voice activity detection.
            silence_limit (int): Duration of silence before stopping the recording.
            inactivity_limit (int): Duration of inactivity before stopping the recording.
            min_recording_length (int): Minimum length of a valid recording.
            buffer_length (int): Length of the audio buffer.
            use_wake_word (bool): Flag to use wake word detection.
            save_wake_word_recordings (bool): If True, saves audio buffer that triggered the wake word detection.
            This can be useful for creating training data for wake word recognition models.

        Dependencies:
            audio_stream_manager (AudioStream): Manages the audio stream.
            wake_word_detector (WakeWordDetector): Handles wake word detection.
            voice_recorder (AudioRecorder): Manages audio recording.
            transcriber (ElevenLabsTranscriber): Transcribes recorded audio.
            action_manager (ActionManager): Manages actions triggered by voice commands.
            recorded_file (str): Path to the last recorded audio file.

        Methods:
            run(transcription=True): Processes a voice command.
            setup(): Initializes the components of the voice processing manager.
            process_voice_command(): Processes a voice command using the configured components.
            """

        logger.debug("Initializing VoiceProcessingManager with provided configurations.")
        if not (0.0 <= sensitivity <= 1.0):
            raise ValueError("Sensitivity must be between 0.0 and 1.0")
        if not (isinstance(rate, int) and rate > 0):
            raise ValueError("Rate must be a positive integer")
        if not (isinstance(channels, int) and channels > 0):
            raise ValueError("Channels must be a positive integer")
        if not (isinstance(frames_per_buffer, int) and frames_per_buffer > 0):
            raise ValueError("Frames per buffer must be a positive integer")
        if not (voice_threshold > 0.0):
            raise ValueError("Voice threshold must be a positive number")
        if not (silence_limit > 0.0):
            raise ValueError("Silence limit must be a positive number")
        if not (inactivity_limit > 0.0):
            raise ValueError("Inactivity limit must be a positive number")
        if not (min_recording_length > 0.0):
            raise ValueError("Minimum recording length must be a positive number")
        if not (buffer_length > 0.0):
            raise ValueError("Buffer length must be a positive number")

        self.wake_word = wake_word
        self.sensitivity = sensitivity
        self.output_directory = output_directory
        self.wake_word_output = wake_word_output
        self.audio_format = audio_format
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.voice_threshold = voice_threshold
        self.silence_limit = silence_limit
        self.inactivity_limit = inactivity_limit
        self.min_recording_length = min_recording_length
        self.buffer_length = buffer_length
        self.use_wake_word = use_wake_word
        self.save_wake_word_recordings = save_wake_word_recordings
        self.play_notification_sound = play_notification_sound

        self.transcriber = transcriber
        self.action_manager = action_manager
        self.audio_stream_manager = audio_stream_manager
        self.wake_word_detector = None
        self.voice_recorder = None

        try:
            self.setup()
        except Exception as e:
            logger.error("Failed to set up VoiceProcessingManager: %s", e)
            raise
        finally:
            self.recorded_file = None

    @classmethod
    def create_default_instance(cls, wake_word='cumputer', sensitivity=0.75, output_directory='Wav_MP3',
                                audio_format=pyaudio.paInt16, channels=1, rate=16000, frames_per_buffer=512,
                                voice_threshold=0.65, inactivity_limit=2.5, min_recording_length=3,
                                buffer_length=2, use_wake_word=True, save_wake_word_recordings=False,
                                play_notification_sound=True):

        """
        Factory method to create a default instance of VoiceProcessingManager with pre-configured dependencies.
        This method simplifies the instantiation process and provides a quick way to get started with common settings.

        Factory method to create a default instance of VoiceProcessingManager with pre-configured dependencies.

        Args:
            wake_word (str): Wake word for triggering voice recording.
            sensitivity (float): Sensitivity for wake word detection.
            output_directory (str): Directory for saving recorded audio files.
            audio_format (int): Format of the audio stream (e.g., pyaudio.paInt16).
            channels (int): Number of audio channels.
            rate (int): Sample rate of the audio stream.
            frames_per_buffer (int): Number of audio frames per buffer.
            voice_threshold (float): Threshold for voice activity detection.
            inactivity_limit (float): Duration of inactivity before stopping the recording.
            min_recording_length (float): Minimum length of a valid recording.
            buffer_length (float): Length of the audio buffer.
            use_wake_word (bool): Flag to use wake word detection.
            save_wake_word_recordings (bool): Flag to save the audio buffer that triggered the wake word detection.
            play_notification_sound (bool): Flag to play notification sound when wake word is detected.

        Returns:
            VoiceProcessingManager: An instance of VoiceProcessingManager with default settings and dependencies.
        """
        transcriber = ElevenLabsTranscriber()
        action_manager = ActionManager()
        audio_stream_manager = AudioStream(rate=rate, channels=channels, _audio_format=audio_format,
                                           frames_per_buffer=frames_per_buffer)
        return cls(transcriber=transcriber, action_manager=action_manager, audio_stream_manager=audio_stream_manager,
                   wake_word=wake_word, sensitivity=sensitivity, output_directory=output_directory,
                   audio_format=audio_format, channels=channels, rate=rate, frames_per_buffer=frames_per_buffer,
                   voice_threshold=voice_threshold, inactivity_limit=inactivity_limit,
                   min_recording_length=min_recording_length, buffer_length=buffer_length, use_wake_word=use_wake_word,
                   save_wake_word_recordings=save_wake_word_recordings or False,
                   play_notification_sound=play_notification_sound)

    def _process_voice_command(self, transcription=True):
        """
        Processes a voice command after wake word detection.

        Args:
            transcription (bool): If True, perform transcription on the recording. Defaults to True.

        Returns:
            str or None: The transcribed text of the voice command, or None if no valid recording was made.
        """
        logger.debug("Starting voice command processing.")
        if self.use_wake_word:
            # Start wake word detection and wait for it to finish
            self.wake_word_detector.run_blocking()
        # Once wake word is detected, start recording
        self.voice_recorder.perform_recording()
        # Wait for the recording to complete
        if self.voice_recorder.recording_thread:
            self.voice_recorder.recording_thread.join()
        # If a recording was made, transcribe it
        if self.voice_recorder.last_saved_file is not None and transcription:
            transcription = self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
            logger.info(f"Transcription: {transcription}")
            return transcription
        logger.debug("Voice command processing completed.")
        return None

    def monitor_active_threads(self):
        """
        Monitors and logs the status of active threads every second.
        """
        try:
            while True:
                active_threads = threading.enumerate()
                logger.info(f"Active threads: {len(active_threads)}")
                for thread in active_threads:
                    logger.info(f"Thread {thread.name} is {'alive' if thread.is_alive() else 'not alive'}.")
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Thread monitoring interrupted by user.")

    def is_stream_closed(self):
        """
        Checks if the audio stream is closed.

        Returns:
            bool: True if the stream is closed, False otherwise.
        """
        return self.audio_stream_manager.is_stream_closed()

    def reinitialize_stream(self):
        """
        Reinitializes the audio stream if it has been closed.
        """
        if self.is_stream_closed():
            self.audio_stream_manager.initialize_stream(self.rate, self.channels, self.audio_format, self.frames_per_buffer)

    def run(self, transcription=True):
        """
        Main method to start the voice processing workflow.

        Processes a voice command after wake word detection.

        Args:
            transcription (bool): If True, perform transcription on the recording. Defaults to True.

        Returns:
            str or None: The transcribed text of the voice command, or None if no valid recording was made.
        """
        logger.info("VoiceProcessingManager run method called.")
        if transcription is False and self.use_wake_word:
            self.wake_word_detector.run_blocking()
            return None
        try:
            transcription_result = None
            self.reinitialize_stream()
            if self.use_wake_word:
                # Initiate wake word detection and block until it completes
                self.wake_word_detector.run_blocking()

            # Once wake word is detected, start recording
            self.voice_recorder.perform_recording()

            # Wait for the recording to complete
            if self.voice_recorder.recording_thread:
                self.voice_recorder.recording_thread.join()

            # Check if a recording was made
            if self.voice_recorder.last_saved_file and transcription:
                # Transcribe the recording
                transcription_result = self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
                logger.info(f"Transcription: {transcription_result}")
            else:
                # If no recording was made or it was too short, log the information
                logger.info("Recording was not made or was too short.")

            # Return the transcription or None if no valid recording was made
            return transcription_result

        except Exception as e:
            logger.exception("An error occurred during voice processing.", exc_info=e)
            raise

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, performing cleanup.")
            thread_manager.shutdown()
            raise  # Re-raise the KeyboardInterrupt to propagate it to the caller


        finally:
            thread_manager.shutdown()
            logger.info("VoiceProcessingManager run method completed.")

    def setup(self):
        """
        Initializes the wake word detector and voice recorder components of the voice processing manager.
        """
        logger.info("Setting up VoiceProcessingManager components.")

        if self.use_wake_word:
            # Initialize WakeWordDetector
            self.wake_word_detector = WakeWordDetector(
                access_key=os.environ.get('PICOVOICE_APIKEY') or os.getenv('PICOVOICE_APIKEY'),
                wake_word=self.wake_word,
                sensitivity=self.sensitivity,
                action_manager=self.action_manager,
                audio_stream_manager=self.audio_stream_manager,
                play_notification_sound=self.play_notification_sound,
                save_audio_directory=self.wake_word_output if self.save_wake_word_recordings else False,
            )
        # Initialize VoiceRecorder
        self.voice_recorder = AudioRecorder(output_directory=self.output_directory,
                                            voice_threshold=self.voice_threshold,
                                            inactivity_limit=self.inactivity_limit,
                                            min_recording_length=self.min_recording_length,
                                            buffer_length=self.buffer_length)
        # Add the voice recorder's thread to the thread manager
        thread_manager.add_thread(self.voice_recorder.recording_thread)

    def process_voice_command(self):
        """
        Processes a voice command using the configured components. It starts with wake word detection, followed by voice recording and transcription.

        Returns:
            str or None: The transcribed text of the voice command, or None if no valid recording was made.
        """
        self.wake_word_detector.run_blocking()

        # Once wake word is detected, start recording
        self.voice_recorder.perform_recording()
        # Wait for the recording to complete
        if self.voice_recorder.recording_thread:
            self.voice_recorder.recording_thread.join()

        # If a recording was made, transcribe it
        if self.voice_recorder.last_saved_file is not None:
            # where the transcrition file recorded is stored
            transcription = self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
            logger.info(f"Transcription: {transcription}")
            return transcription

        return None
