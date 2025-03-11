import logging
import os
import threading
import time
import signal

import pyaudio

from VoiceProcessingToolkit.transcription.elevenlabs import ElevenLabsTranscriber
from VoiceProcessingToolkit.wake_word_detector.AudioStreamManager import AudioStream
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager
from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
from VoiceProcessingToolkit.shared_resources import thread_manager
from VoiceProcessingToolkit.config import get_config

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
    def create_default_instance(cls, **kwargs) -> 'VoiceProcessingManager':
        """
        Create a default instance of the voice processing manager with default configurations.
        
        Args:
            **kwargs: Additional arguments to override default configurations.
                voice_threshold (float, optional): Threshold for Cobra VAD voice detection.
                inactivity_limit (float, optional): Seconds of inactivity before stopping recording.
                min_recording_length (float, optional): Minimum recording length for a valid sample.
                buffer_length (float, optional): Length of audio buffer in seconds.
                use_cobra_vad (bool, optional): Whether to use Cobra VAD instead of energy-based detection.
                
                Other general parameters can also be provided:
                wake_word (str, optional): Wake word to detect.
                sensitivity (float, optional): Sensitivity for wake word detection.
                output_dir (str, optional): Directory for saving recordings.
                access_key (str, optional): Access key for wake word detection.
                transcriber_api_key (str, optional): API key for the transcriber.
            
        Returns:
            VoiceProcessingManager: A new instance with default or overridden settings.
        """
        # Extract Cobra VAD specific parameters if provided
        cobra_params = {}
        if 'voice_threshold' in kwargs:
            cobra_params['voice_threshold'] = kwargs.pop('voice_threshold')
        if 'inactivity_limit' in kwargs:
            cobra_params['inactivity_limit'] = kwargs.pop('inactivity_limit')
        if 'min_recording_length' in kwargs:
            cobra_params['min_recording_length'] = kwargs.pop('min_recording_length')
        if 'buffer_length' in kwargs:
            cobra_params['buffer_length'] = kwargs.pop('buffer_length')
        
        # Create instance
        instance = cls(
            ElevenLabsTranscriber(),
            ActionManager(),
            AudioStream(rate=kwargs.get('rate', 16000), channels=kwargs.get('channels', 1), _audio_format=kwargs.get('audio_format', pyaudio.paInt16), frames_per_buffer=kwargs.get('frames_per_buffer', 512)),
            kwargs.get('wake_word', 'computer'),
            kwargs.get('sensitivity', 0.75),
            kwargs.get('output_directory', 'Wav_MP3'),
            kwargs.get('wake_word_output', 'wake_word_output'),
            kwargs.get('audio_format', pyaudio.paInt16),
            kwargs.get('channels', 1),
            kwargs.get('rate', 16000),
            kwargs.get('frames_per_buffer', 512),
            kwargs.get('voice_threshold', 0.8),
            kwargs.get('silence_limit', 2.0),
            kwargs.get('inactivity_limit', 2.0),
            kwargs.get('min_recording_length', 2.0),
            kwargs.get('buffer_length', 2.0),
            kwargs.get('use_wake_word', True),
            kwargs.get('save_wake_word_recordings', False),
            kwargs.get('play_notification_sound', True)
        )
        
        # Apply Cobra VAD parameters to voice_recorder if it exists
        if instance.voice_recorder and cobra_params:
            for param, value in cobra_params.items():
                setattr(instance.voice_recorder, param, value)
        
        return instance

    def _process_voice_command(self, transcription=True):
        """
        Process a voice command with wake word detection.
        
        Args:
            transcription (bool, optional): Whether to transcribe the recording. Defaults to True.
            
        Returns:
            str or None: Transcription result if available.
        """
        logger.debug("Processing voice command with wake word detection")
        
        # Initiate wake word detection and block until it completes
        self.wake_word_detector.run_blocking()
        
        if not transcription:
            return None
            
        # Once wake word is detected, start recording
        self.voice_recorder.perform_recording()
        
        # Wait for the recording to complete with a timeout
        if self.voice_recorder.recording_thread:
            self.voice_recorder.recording_thread.join(timeout=60.0)
            if self.voice_recorder.recording_thread.is_alive():
                logger.warning("Recording thread did not complete within the timeout period.")
        
        # Check if a recording was made
        if self.voice_recorder.last_saved_file:
            # Transcribe the recording
            logger.info(f"Transcribing file: {self.voice_recorder.last_saved_file}")
            transcription_result = self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
            logger.info(f"Transcription result: {transcription_result}")
            return transcription_result
        else:
            # If no recording was made or it was too short, log the information
            logger.info("Recording was not made or was too short.")
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
        Run the voice processing pipeline.

        Args:
            transcription (bool, optional): Flag to indicate whether to perform transcription. Defaults to True.

        Returns:
            str or None: The transcription result, if available.
        """
        try:
            self.setup()
            
            # Register a cleanup handler for SIGINT
            signal_handler = signal.getsignal(signal.SIGINT)
            def cleanup_handler(sig, frame):
                logger.info("Received interrupt signal, cleaning up...")
                self.cleanup()
                # Call the original handler, if it exists
                if signal_handler and callable(signal_handler):
                    signal_handler(sig, frame)
            signal.signal(signal.SIGINT, cleanup_handler)
            
            if self.use_wake_word:
                logger.info(f"Running with wake word detection. Wake word: {self.wake_word}")
                return self._process_voice_command(transcription)
            else:
                logger.info("Running without wake word detection.")
                self.voice_recorder.perform_recording()
                
                # Wait for the recording to complete with a timeout
                if self.voice_recorder.recording_thread:
                    self.voice_recorder.recording_thread.join(timeout=60.0)
                    if self.voice_recorder.recording_thread.is_alive():
                        logger.warning("Recording thread did not complete within the timeout period. Continuing anyway.")
                
                transcription_result = None
                if transcription and self.voice_recorder.last_saved_file:
                    logger.info(f"Transcribing file: {self.voice_recorder.last_saved_file}")
                    transcription_result = self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
                    logger.info(f"Transcription result: {transcription_result}")
                
                return transcription_result

        except Exception as e:
            logger.exception("An error occurred during voice processing.", exc_info=e)
            self.cleanup()
            raise

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, performing cleanup.")
            self.cleanup()
            raise  # Re-raise the KeyboardInterrupt to propagate it to the caller


        finally:
            self.cleanup()
            logger.info("VoiceProcessingManager run method completed.")
            
    def cleanup(self):
        """
        Properly clean up all resources.
        
        This method should be called before the program exits to ensure proper resource cleanup.
        """
        logger.info("Cleaning up resources...")
        
        # Clean up thread manager
        try:
            thread_manager.shutdown()
        except Exception as e:
            logger.error(f"Error during thread manager shutdown: {e}")
        
        # Clean up wake word detector if it exists
        if hasattr(self, 'wake_word_detector') and self.wake_word_detector:
            try:
                if hasattr(self.wake_word_detector, 'cleanup'):
                    self.wake_word_detector.cleanup()
            except Exception as e:
                logger.error(f"Error during wake word detector cleanup: {e}")
        
        # Clean up voice recorder if it exists
        if hasattr(self, 'voice_recorder') and self.voice_recorder:
            try:
                if hasattr(self.voice_recorder, 'cleanup'):
                    self.voice_recorder.cleanup()
            except Exception as e:
                logger.error(f"Error during voice recorder cleanup: {e}")
        
        # Clean up audio stream manager if it exists
        if hasattr(self, 'audio_stream_manager') and self.audio_stream_manager:
            try:
                if hasattr(self.audio_stream_manager, 'cleanup'):
                    self.audio_stream_manager.cleanup()
            except Exception as e:
                logger.error(f"Error during audio stream manager cleanup: {e}")
        
        logger.info("Cleanup completed.")

    def setup(self) -> None:
        """
        Initialize the components of the voice processing manager if not already done.
        """
        # Validate API keys
        picovoice_apikey = os.environ.get('PICOVOICE_APIKEY') or os.getenv('PICOVOICE_APIKEY')
        elevenlabs_apikey = os.environ.get('ELEVENLABS_API_KEY') or os.getenv('ELEVENLABS_API_KEY')
        
        # Check for required API keys if wake word detection is enabled
        if self.use_wake_word and not picovoice_apikey:
            logger.error("PICOVOICE_APIKEY environment variable is not set. Wake word detection will not work.")
            raise ValueError("PICOVOICE_APIKEY environment variable is required for wake word detection.")
        
        # Create wake word detector if not provided
        if self.wake_word_detector is None:
            logger.info("Creating default wake word detector")
            self.wake_word_detector = WakeWordDetector(
                access_key=picovoice_apikey,
                wake_word=self.wake_word,
                sensitivity=self.sensitivity,
                action_manager=self.action_manager,
                audio_stream_manager=self.audio_stream_manager,
                play_notification_sound=self.play_notification_sound,
                save_audio_directory=self.wake_word_output if self.save_wake_word_recordings else False,
            )
        
        # Create voice recorder if not provided
        if self.voice_recorder is None:
            logger.info("Creating default voice recorder")
            # Use the configuration for either Cobra VAD or energy-based detection
            try:
                config = get_config()
                if config.audio.use_cobra_vad:
                    if not picovoice_apikey:
                        logger.warning("PICOVOICE_APIKEY not set. Falling back to energy-based voice detection.")
                        self.voice_recorder = AudioRecorder(output_dir=self.output_directory)
                    else:
                        logger.info("Using Cobra VAD for voice detection")
                        self.voice_recorder = AudioRecorder(
                            output_dir=self.output_directory,
                            voice_threshold=config.audio.voice_threshold,
                            inactivity_limit=config.audio.inactivity_limit,
                            min_recording_length=config.audio.min_recording_length,
                            buffer_length=config.audio.buffer_length
                        )
                else:
                    logger.info("Using energy-based voice detection")
                    self.voice_recorder = AudioRecorder(output_dir=self.output_directory)
            except Exception as e:
                logger.warning(f"Error reading configuration: {e}. Using default energy-based voice detection.")
                self.voice_recorder = AudioRecorder(output_dir=self.output_directory)
        
        # Create transcriber if not provided
        if self.transcriber is None:
            logger.info("Creating default transcriber")
            if not elevenlabs_apikey:
                logger.error("ELEVENLABS_API_KEY environment variable is not set. Transcription will not work.")
                raise ValueError("ELEVENLABS_API_KEY environment variable is required for transcription.")
                
            self.transcriber = ElevenLabsTranscriber(
                api_key=elevenlabs_apikey
            )

    def process_voice_command(self):
        """
        Processes a voice command using the configured components. It starts with wake word detection, followed by voice recording and transcription.

        Returns:
            str or None: The transcribed text of the voice command, or None if no valid recording was made.
        """
        self.wake_word_detector.run_blocking()

        # Once wake word is detected, start recording
        self.voice_recorder.perform_recording()
        
        # Wait for the recording to complete with a timeout to prevent hanging
        if self.voice_recorder.recording_thread:
            # Add a reasonable timeout (e.g., 60 seconds) to prevent hanging
            self.voice_recorder.recording_thread.join(timeout=60.0)
            if self.voice_recorder.recording_thread.is_alive():
                logger.warning("Recording thread did not complete within the timeout period. Continuing anyway.")

        # If a recording was made, transcribe it
        if self.voice_recorder.last_saved_file is not None:
            # where the transcrition file recorded is stored
            transcription = self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
            logger.info(f"Transcription: {transcription}")
            return transcription

        return None
