import logging
import asyncio
import time

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager

# Basic configuration
logging.basicConfig(level=logging.INFO)

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
        vpm = VoiceProcessingManager.create_default_instance(use_wake_word=True, save_wake_word_recordings=True, play_notification_sound=False)

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