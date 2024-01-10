import logging
import os
import pyaudio
from dotenv import load_dotenv
from elevenlabs import generate, stream

from VoiceProcessingToolkit.transcription.whisper import WhisperTranscriber
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector, AudioStream
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager
from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
from VoiceProcessingToolkit.text_to_speech.elevenlabs_tts import ElevenLabsTextToSpeech, ElevenLabsConfig
from shared_resources import thread_manager

logger = logging.getLogger(__name__)



def text_to_speech(text, config=None, output_dir=None, voice_id=None, api_key=None):
    """
    Converts text to speech using the ElevenLabs API.

    This function synthesizes speech from the given text using ElevenLabs' text-to-speech technology. It handles
    the creation of an ElevenLabsTextToSpeech object and manages the API key retrieval from the environment
    variable or the provided parameter.

    Args:
        text (str): Text to be converted to speech.
        config (ElevenLabsConfig, optional): Configuration object for ElevenLabs TTS.
        output_dir (str, optional): Directory to save the output audio file. Defaults to 'audio_files'.
        voice_id (str, optional): Specific voice ID for speech synthesis.
        api_key (str, optional): API key for ElevenLabs, if not provided in config.

    Returns:
        str or None: File path to the saved audio file, or None if synthesis fails.
    """
    if config is None:
        config = ElevenLabsConfig(voice_id=voice_id, api_key=api_key or None)
    tts = ElevenLabsTextToSpeech(config=config, voice_id=voice_id)
    return tts.synthesize_speech(text, output_dir)


def text_to_speech_stream(text, config=None, voice_id=None, api_key=None):
    """
    Streams synthesized speech from text using the ElevenLabs API.

    This function streams synthesized speech directly without saving it to a file. It's useful for real-time
    applications where immediate audio playback is required.

    Args:
        text (str): Text to be converted into speech for streaming.
        config (ElevenLabsConfig, optional): Configuration for ElevenLabs API.
        voice_id (str, optional): The ID of the voice to use for speech synthesis.
        api_key (str, optional): API key for accessing ElevenLabs services.

    Returns:
        None
    """
    if config is None:
        config = ElevenLabsConfig(api_key=api_key or None)
    if not text:
        logging.info("No text provided for synthesis.")
        return

    # Ensure text-to-speech is enabled
    if not config.enable_text_to_speech:
        logging.info("Text-to-speech is disabled in settings.")
        return

    try:
        # Generate the audio stream
        audio_stream = generate(
            text=text,
            voice=voice_id or config.voice_id,
            model=config.model_id,
            api_key=config.elevenlabs_api_key,
            stream=True  # Enable streaming
        )

        # Stream the audio if playback is enabled
        if config.playback_enabled:
            stream(audio_stream)
    except Exception as e:
        logging.exception(f"An error occurred during streaming text-to-speech: {e}")


class VoiceProcessingManager:
    def __init__(self, wake_word='jarvis', sensitivity=0.5, output_directory='Wav_MP3',
                 audio_format=pyaudio.paInt16, channels=1, rate=16000, frames_per_buffer=512,
                 voice_threshold=0.8, silence_limit=2, inactivity_limit=2, min_recording_length=3, buffer_length=2,
                 use_wake_word=True):
        """
        Initializes the voice processing manager with the given configuration.

            Manages the voice processing pipeline, including wake word detection, voice recording, and transcription.

            This class integrates different components such as wake word detection, voice recording, and speech transcription.
            It provides a high-level interface to manage the flow of processing voice commands.

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

            Dependencies:
                audio_stream_manager (AudioStream): Manages the audio stream.
                wake_word_detector (WakeWordDetector): Handles wake word detection.
                voice_recorder (AudioRecorder): Manages audio recording.
                transcriber (WhisperTranscriber): Transcribes recorded audio.
                action_manager (ActionManager): Manages actions triggered by voice commands.
                recorded_file (str): Path to the last recorded audio file.
                elevenlabs_config (ElevenLabsConfig): Configuration for ElevenLabs text-to-speech service.

            Methods:
                run(tts=False, streaming=False): Processes a voice command with optional text-to-speech functionality.
                setup(): Initializes the components of the voice processing manager.
                process_voice_command(): Processes a voice command using the configured components.
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
        self.use_wake_word = use_wake_word  # Initialize use_wake_word here

        self.audio_stream_manager = None
        self.wake_word_detector = None
        self.voice_recorder = None
        self.transcriber = WhisperTranscriber()
        self.action_manager = ActionManager()

        self.setup()
        self.recorded_file = None

    def _process_voice_command(self, streaming=False, tts=False, api_key=None, voice_id=None):
        # Processes a voice command after wake word detection and optionally performs text-to-speech on the transcription.
        """
        Processes a voice command after wake word detection and optionally performs text-to-speech on the transcription.
        Allows for passing an optional API key and voice ID for text-to-speech customization.

        Args:
            streaming (bool): If True, use streaming text-to-speech. Defaults to False.
            tts (bool): If True, perform text-to-speech on the transcription. Defaults to False.
            api_key (str, optional): API key for ElevenLabs, if not provided in config.
            voice_id (str, optional): Specific voice ID for speech synthesis.

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
        if self.voice_recorder.last_saved_file is not None:
            transcription = self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
            logger.info(f"Transcription: {transcription}")
            if transcription and tts:
                if streaming:
                    text_to_speech_stream(transcription, api_key=api_key, voice_id=voice_id)
                else:
                    text_to_speech(transcription, api_key=api_key, voice_id=voice_id)
            return transcription
        return None

    def run(self, tts=False, streaming=False, api_key=None, voice_id=None):
        """
        The main entry point for the VoiceProcessingManager. It processes a voice command after wake word detection.
        Optionally performs text-to-speech on the transcription and can stream the synthesized speech. It also allows
        for passing an optional API key and voice ID for text-to-speech customization.

        Args:
            tts (bool): If True, perform text-to-speech on the transcription. Defaults to False.
            streaming (bool): If True, use streaming text-to-speech. Defaults to False. Only relevant if tts is True.
            api_key (str, optional): API key for ElevenLabs, if not provided in config.
            voice_id (str, optional): Specific voice ID for speech synthesis.

        Returns:
            str or None: The transcribed text of the voice command, or None if no valid recording was made.
        """
        try:
            transcription = self._process_voice_command(streaming=streaming, tts=tts, api_key=api_key, voice_id=voice_id)
            if not tts:
                return transcription
            # If tts is True, the text-to-speech is already handled in _process_voice_command
            # Ensure all threads are joined before exiting
            thread_manager.join_all()
        except Exception as e:
            logger.exception(f"An error occurred during voice processing: {e}")
            raise

    def setup(self):
        # Initialize AudioStream
        """
        Initializes the components of the voice processing manager, including audio stream, wake word detector, and voice recorder.
        """
        self.audio_stream_manager = AudioStream(rate=self.rate, channels=self.channels,
                                                _audio_format=self.audio_format,
                                                frames_per_buffer=self.frames_per_buffer)

        if self.use_wake_word:
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

        # If no recording was made, return None
        return None

def main():
    load_dotenv()
    try:
        vpm = VoiceProcessingManager(sensitivity=0.5, use_wake_word=True)
        text = vpm.run(tts=True, streaming=False)
        logger.info(f"Text: {text}")

    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, shutting down gracefully.")
    finally:
        thread_manager.shutdown()
        logger.info("Exiting main function.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
