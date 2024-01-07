import os
import logging
from elevenlabs import generate, stream

# Constants
ELEVENLABS_API_URL = 'https://api.elevenlabs.io/v1/text-to-speech/'
ELEVENLABS_MODEL_ID = 'eleven_monolingual_v1'

# Configuration class
class ElevenLabsConfig:
    def __init__(self, api_key=None, voice_id=None, model_id=None, playback_enabled=True):
        self.api_key = os.getenv('ELEVENLABS_API_KEY', api_key) or api_key
        self.voice_id = voice_id or "eqI1AF0IrvwU3tgfmt0B"
        self.model_id = model_id or ELEVENLABS_MODEL_ID
        self.playback_enabled = playback_enabled

        if not self.api_key:
            raise ValueError("API key is required for ElevenLabsTextToSpeech.")

    def load_settings(self, settings_file='config/settings.json'):
        # Existing settings loading implementation

class ElevenLabsTextToSpeech:
    def __init__(self, config=None):
        self.config = config or ElevenLabsConfig()

    def synthesize_speech(self, text):
        if not text or text == 'NO_VOICE_EXIT':
            return None

        audio_stream = generate(
            text=text,
            voice=self.config.voice_id,
            model=self.config.model_id,
            api_key=self.config.api_key,
            stream=True
        )

        # Stream the audio if playback is enabled
        if self.config.playback_enabled:
            stream(audio_stream)

        return audio_stream

def text_to_speech(text, voice_id=None):
    config = ElevenLabsConfig(voice_id=voice_id)
    tts = ElevenLabsTextToSpeech(config=config)
    return tts.synthesize_speech(text)

# Example usage
if __name__ == "__main__":
    audio_stream = text_to_speech("Hello, this is a test of the ElevenLabs streaming text to speech API.")
