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
    Synthesizes speech from text using ElevenLabs API with minimal configuration required from the user.

    This function serves as a simple and direct way to convert text to speech, handling the instantiation of the
    ElevenLabsTextToSpeech class and the retrieval of the API key from the ELEVENLABS_API_KEY environment variable.
    If the output directory is not specified, the audio file will be saved in a default 'audio_files' directory.

    Args:
        text (str): The text to be converted into speech.
        output_dir (str, optional): The directory where the audio file will be saved. Defaults to None.
        config (ElevenLabsConfig, optional): The configuration for ElevenLabs TTS. If not provided, defaults will be used.

    Returns:
        str: The file path to the saved audio file if the synthesis was successful, None otherwise.
        :param text:
        :param output_dir:
        :param voice_id:
    """
    if config is None:
        config = ElevenLabsConfig(voice_id=voice_id, api_key=api_key or None)
    tts = ElevenLabsTextToSpeech(config=config, voice_id=voice_id)
    return tts.synthesize_speech(text, output_dir)


def text_to_speech_stream(text, config=None, voice_id=None, api_key=None):
    """
    Streams synthesized speech from text using ElevenLabs API.

    Args:
        text (str): The text to be converted into speech.
        config (ElevenLabsConfig, optional): Configuration for ElevenLabs API. If not provided, defaults will be used.
        voice_id (str, optional): The ID of the voice to be used for speech synthesis. Overrides the voice_id in config if provided.
        :param text:
        :param config:
        :param voice_id:
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
        self.recorded_file = None

    def recorder_transcriber(self):
        """
        Method to record a voice command and return the transcription without wake word detection.

        Returns:
            str or None: The transcribed text of the voice command, or None if no valid recording was made.
        """
        # Start recording
        self.voice_recorder.perform_recording()

        # If a recording was made, transcribe it
        if self.voice_recorder.last_saved_file:
            transcription = self.transcriber.transcribe_audio(self.voice_recorder.last_saved_file)
            return transcription

        # If no recording was made, return None
        return None

    def wakeword_tts(self, streaming=None):
        """
        Method to process a voice command after wake word detection and perform text-to-speech on the transcription.
        """
        transcription = self.process_voice_command()
        if transcription:
            logger.info(f"Transcription: {transcription}")
            if streaming is False:
                text_to_speech(transcription)
            else:
                text_to_speech_stream(transcription)
        else:
            logger.info("No transcription was made.")
        # Ensure all threads are joined before exiting the method
        thread_manager.join_all()

    def wakeword_transcription(self):
        """
        Method to process a voice command after wake word detection and return the transcription.

        Returns:
            str or None: The transcribed text of the voice command, or None if no valid recording was made.
        """
        transcription = self.process_voice_command()
        if transcription:
            logger.info(f"Transcription: {transcription}")
        else:
            logger.info("No transcription was made.")
            return transcription
        # Ensure all threads are joined before exiting the method
        thread_manager.join_all()

    def process_voice_command(self):
        # Start wake word detection and wait for it to finish
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
        # Add the voice recorder's thread to the thread manager
        thread_manager.add_thread(self.voice_recorder.recording_thread)


def main():
    load_dotenv()
    vpm = VoiceProcessingManager()
    vpm.wakeword_tts()
    thread_manager.join_all()
    logger.info("Exiting main function.")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
