import json
import logging
import os
import tempfile
import time

import pygame
from dotenv import load_dotenv

import requests


# Constants
ELEVENLABS_API_URL = 'https://api.elevenlabs.io/v1/text-to-speech/'
ELEVENLABS_MODEL_ID = 'eleven_monolingual_v1'


# Configuration class
class ElevenLabsConfig:
    # The API key forElevenLabs can be provided as an argument or set as an environment variable 'ELEVENLABS_API_KEY'.
    def __init__(self, api_key=None, voice_id=None, model_id=None, playback_enabled=True):
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY', api_key) or api_key
        self.voice_id = voice_id or "eqI1AF0IrvwU3tgfmt0B"
        self.model_id = model_id or ELEVENLABS_MODEL_ID
        self.enable_text_to_speech = True
        self.playback_enabled = playback_enabled

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
        self.mixer_initialized = None
        self.temp_dir = None
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

        # Check if output_dir is provided or not
        use_temp_dir = output_dir is None

        if use_temp_dir:
            # Use a temporary directory to store and play the audio
            temp_dir = tempfile.TemporaryDirectory()
            output_dir = temp_dir.name

        os.makedirs(output_dir, exist_ok=True)

        try:
            logging.debug("Sending request to ElevenLabs API for text-to-speech synthesis")
            response = requests.post(ELEVENLABS_API_URL + voice_id, headers=headers, json=data)
            logging.debug("Received response from ElevenLabs API with status code: %s", response.status_code)
            if response.status_code == 200:
                # Define the output file path
                output_file = os.path.join(output_dir, 'output.mp3')
                with open(output_file, 'wb') as f:
                    f.write(response.content)

                logging.info(f"Audio file created at: {output_file}")

                # Initialize pygame mixer and play audio file if playback is enabled
                if config.playback_enabled:
                    pygame.mixer.init()
                    self.mixer_initialized = True
                    pygame.mixer.music.load(output_file)
                    pygame.mixer.music.play()

                    # Wait for the playback to finish if using a temporary directory
                    if use_temp_dir:
                        while pygame.mixer.music.get_busy():
                            time.sleep(1)

                    pygame.mixer.quit()
                    self.mixer_initialized = False

                    # If using a temporary directory, the file will be deleted upon exiting the context
                    if output_dir is None:
                        # Cleanup the temporary directory after playback
                        self.temp_dir.cleanup()
                        self.temp_dir = None
                        return None
                return output_file if not use_temp_dir else None
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
        
    def stop_playback(self):
        """
        Stops the audio playback if it is currently playing.
        """
        if self.mixer_initialized and pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            self.mixer_initialized = False
            if self.temp_dir:
                self.temp_dir.cleanup()
                self.temp_dir = None

if __name__ == '__main__':
    load_dotenv()
    logging.basicConfig(level=logging.DEBUG)

