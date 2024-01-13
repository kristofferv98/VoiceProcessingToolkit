import logging
import os
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """
    WhisperTranscriber handles transcription using OpenAI's Whisper ASR system.
    """

    def __init__(self):
        # The API key for OpenAI's Whisper ASR system can be set as an environment variable 'OPENAI_API_KEY'.
        load_dotenv()
        self.client = OpenAI()

    def transcribe_audio(self, audio_filepath):
        """
        Translates and transcribes a non-English audio file into English text using OpenAI's Whisper ASR system.

        Args:
            audio_filepath (str): Path to the audio file.

        Returns:
            str: Translated and transcribed text if successful, None otherwise.
        """
        # Check if the audio file exists
        try:
            if not os.path.exists(audio_filepath):
                raise FileNotFoundError(f"Error: File '{audio_filepath}' does not exist.")
        except FileNotFoundError as e:
            logger.exception("File not found: %s", e)
            raise

        try:
            with open(audio_filepath, "rb") as audio_file:
                logging.debug("Sending audio file to Whisper API for transcription")
                # Create translation and transcription
                transcript = self.client.audio.translations.create(
                    model="whisper-1",
                    file=audio_file
                )
                logging.debug("Received transcription response from Whisper API")
        except Exception as e:
            logging.exception("An error occurred during the transcription process: %s", e)
            raise
        else:
            # Access the translated and transcribed text
            transcription_text = getattr(transcript, "text", None)
            if transcription_text is not None:
                transcription_text = transcription_text.strip()
            logging.info(f"Transcription: {transcription_text}")
            return transcription_text


if __name__ == '__main__':
    audio_path = "path_to_audio.mp3"
    transcriber = WhisperTranscriber()
    transcription = transcriber.transcribe_audio(audio_path)
    if transcription:
        logging.info(f"Transcription: {transcription}")
