from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from dotenv import load_dotenv

import logging
import os

#logging.basicConfig(level=logging.INFO)
load_dotenv()

# Set environment variables for API keys
os.getenv('PICOVOICE_APIKEY')
os.getenv('OPENAI_API_KEY')
os.getenv('ELEVENLABS_API_KEY')

def main():
    """
    Demonstrates the basic usage of the WakeWordDetector to create a wake word dataset.

    This script initializes the VoiceProcessingManager with defined settings with the save_wake_word_recordings flag.
    This will create a folder called "wake_word_dataset" in the current working directory and save the wake word
    usage during usage. This can be used to create a wake word dataset for the wake word detector, based on normal
    usage as the usage of the wake word detector as it will not be affected by the recording of the wake word.
    The script can be terminated early by a KeyboardInterrupt (Ctrl+C).
    """

    try:
        # Create a WakeWordDetector instance with default settings
        wake_word_detector = VoiceProcessingManager.create_default_instance(use_wake_word=True, wake_word='computer',
                                                                            save_wake_word_recordings=True,
                                                                            play_notification_sound=False)

        # Run the wake word detector
        wake_word_detector.run(transcription=False)

    except KeyboardInterrupt:
        logging.info("Interrupted by user, shutting down.")


if __name__ == '__main__':
    main()
