from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from dotenv import load_dotenv

import asyncio
import os
import time
import logging

# logging.basicConfig(level=logging.INFO)
load_dotenv()
logging.basicConfig(level=logging.INFO)

# Set environment variables for API keys in .env file
os.getenv('PICOVOICE_APIKEY')
os.getenv('OPENAI_API_KEY')
os.getenv('ELEVENLABS_API_KEY')


def main():
    """
    Demonstrates the basic usage of the VoiceProcessingManager.

    This script initializes the VoiceProcessingManager with default settings and runs it to process a voice command.
    It also demonstrates how to register actions with the VoiceProcessingManager that will be triggered when the
    wake word is detected. The processed text is printed to the console. The script uses text-to-speech
    functionality without streaming.

    The script can be terminated early by a KeyboardInterrupt (Ctrl+C).
    """
    try:
        # Create a VoiceProcessingManager instance with default settings
        vpm = VoiceProcessingManager.create_default_instance(
            use_wake_word=True,
            wake_word="computer",
            save_wake_word_recordings=True,
            play_notification_sound=True,
        )

        @vpm.action_manager.register_action
        def action_with_notification():
            logging.info("Sync function is running...")
            time.sleep(4.5)

        @vpm.action_manager.register_action
        async def async_action():
            logging.info("Async function is running...")
            await asyncio.sleep(1)  # Simulate an async wait

        # Run the voice processing manager with text-to-speech and streaming
        vpm.run(tts=True, streaming=True)

    except KeyboardInterrupt:
        logging.info("Interrupted by user, shutting down.")


if __name__ == '__main__':
    main()
