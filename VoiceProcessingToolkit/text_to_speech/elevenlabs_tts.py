import json
import logging
import os
import tempfile

from dotenv import load_dotenv
from elevenlabs import generate, stream

import requests


# Constants
ELEVENLABS_API_URL = 'https://api.elevenlabs.io/v1/text-to-speech/'
ELEVENLABS_MODEL_ID = 'eleven_monolingual_v1'


# Configuration class
class ElevenLabsConfig:
    def __init__(self, api_key=None, voice_id=None, model_id=None, playback_enabled=True):
        # The API key for ElevenLabs can be provided as an argument or set as an environment variable
        # 'ELEVENLABS_API_KEY'.
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY', api_key) or api_key
        self.voice_id = voice_id or "eqI1AF0IrvwU3tgfmt0B"
        self.model_id = model_id or ELEVENLABS_MODEL_ID
        self.enable_text_to_speech = True
        self.playback_enabled = playback_enabled

        if not self.elevenlabs_api_key:
            raise ValueError("API key is required for ElevenLabsTextToSpeech.")

        if not self.elevenlabs_api_key:
            raise ValueError("API key is required for ElevenLabsTextToSpeech.")

    def load_settings(self, settings_file='config/settings.json'):
        try:
            with open(settings_file, 'r') as f:
                settings = json.load(f)
                self.voice_id = settings.get('voice_id')
                self.enable_text_to_speech = settings.get('enable_text_to_speech', True)
        except FileNotFoundError:
            logging.warning(f"Settings file {settings_file} not found. Using defaults.")


class ElevenLabsTextToSpeech:
    def __init__(self, config=None, voice_id=None):
        self.config = config or ElevenLabsConfig(voice_id=voice_id)

    def synthesize_speech(self, text, output_dir=None):
        """
        Converts text to speech using ElevenLabs API.

        Args:
            text (str): The text to convert to speech.
            output_dir (str, optional): The directory to save the audio file. Defaults to None.

        Returns:
            str: Path to the audio file if successful, None otherwise.
        """
        config = self.config
        if not config.enable_text_to_speech:
            logging.info("Text-to-speech is disabled in settings.")
            return None
        if text is None or text == 'NO_VOICE_EXIT' or text == '':
            return None

        # Remove asterisks and hashes from the text
        text = text.replace('*', '').replace('#', '')

        voice_id = config.voice_id or 'default_voice_id'
        headers = {
            'Accept': 'audio/mpeg',
            'xi-api-key': config.elevenlabs_api_key,
            'Content-Type': 'application/json'
        }
        data = {
            'text': text,
            'model_id': ELEVENLABS_MODEL_ID,
            'voice_settings': {
                'stability': 0.85,
                'similarity_boost': 0.85
            }
        }

        # Ensure the output directory exists
        if not output_dir:
            temp_dir = tempfile.TemporaryDirectory()
            output_dir = temp_dir.name
            os.makedirs(output_dir, exist_ok=True)
        else:
            # Ensure the specified output directory exists
            os.makedirs(output_dir, exist_ok=True)

        try:
            logging.debug("Sending request to ElevenLabs API for text-to-speech synthesis")
            response = requests.post(ELEVENLABS_API_URL + voice_id, headers=headers, json=data)
            logging.debug("Received response from ElevenLabs API with status code: %s", response.status_code)
            if response.status_code == 200:
                # The output directory is guaranteed to exist at this point
                output_file = os.path.join(output_dir, 'output.mp3')
                with open(output_file, 'wb') as f:
                    f.write(response.content)

                logging.info(f"Audio file created at: {output_file}")

                # Initialize pygame mixer and play audio file if playback is enabled
                if config.playback_enabled:
                    return output_file
            else:
                error_message = f"API Error: Status code {response.status_code}. Response: {response.text}"
                if response.status_code == 401:
                    logging.error(f"Authentication failed: {error_message}")
                else:
                    logging.error(f"Unexpected error occurred: {error_message}")
                return None
        except Exception as e:
            logging.exception(f"An error occurred in text_to_speech: {e}")
            return None


def text_to_speech(text, output_dir=None, voice_id=None):
    """
    Synthesizes speech from text using ElevenLabs API with minimal configuration required from the user.

    This function serves as a simple and direct way to convert text to speech, handling the instantiation of the
    ElevenLabsTextToSpeech class and the retrieval of the API key from the ELEVENLABS_API_KEY environment variable.
    If the output directory is not specified, the audio file will be saved in a default 'audio_files' directory.

    Args:
        text (str): The text to be converted into speech.
        output_dir (str, optional): The directory where the audio file will be saved. Defaults to None.

    Returns:
        str: The file path to the saved audio file if the synthesis was successful, None otherwise.
        :param text:
        :param output_dir:
        :param voice_id:
    """
    tts = ElevenLabsTextToSpeech(voice_id=voice_id)
    return tts.synthesize_speech(text, output_dir)


def text_to_speech_stream(text, config=None, voice_id=None):

def text_to_speech_stream(text, config=None, voice_id=None):
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
        config = ElevenLabsConfig()
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



if __name__ == '__main__':
    load_dotenv()
    logging.basicConfig(level=logging.DEBUG)
    text_to_speech_stream("""EXAMPLE""")

