from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from dotenv import load_dotenv

import os
import logging

#logging.basicConfig(level=logging.INFO)
load_dotenv()

# Set environment variables for API keys in .env file
os.getenv('PICOVOICE_APIKEY')
os.getenv('OPENAI_API_KEY')
os.getenv('ELEVENLABS_API_KEY')

def main():
    """
    Demonstrates a custom usage of the VoiceProcessingManager.

    This script initializes the VoiceProcessingManager with custom recording settings and runs it without the wake word
    detector or text-to-speech functionality. This wil result in a recording with transcription that runs until the
    custom logic in the action manager is completed.

    The processed text is printed to the console.

    """

    # Create a VoiceProcessingManager instance with custom settings
    vpm = VoiceProcessingManager.create_default_instance(use_wake_word=False, voice_threshold=0.5, inactivity_limit=5,
                                                         min_recording_length=2)

    # Run the voice processing manager with text-to-speech but without streaming and without wake word detection
    text = vpm.run(tts=False, transcription=True)

    print(f"Processed text: {text}")


if __name__ == '__main__':
    main()
