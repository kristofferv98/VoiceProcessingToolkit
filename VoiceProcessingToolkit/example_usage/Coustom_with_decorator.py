import logging
import asyncio
import time

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager

# Basic configuration
logging.basicConfig(level=logging.INFO)

def main():
    """
    Demonstrates a more advanced and customizable usage of the VoiceProcessingManager using decorators.

    In this example, the VoiceProcessingManager is initialized with default settings. Additionally, custom actions are
    defined and registered using decorators. These actions are triggered during the voice processing workflow.

    The script showcases asynchronous action handling and can be terminated early by a KeyboardInterrupt (Ctrl+C).
    """
    try:
        # Create a VoiceProcessingManager instance with default settings
        vpm = VoiceProcessingManager.create_default_instance()

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
