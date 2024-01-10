import logging
from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager

# Basic configuration
logging.basicConfig(level=logging.INFO)


def main():
    """
    Demonstrates the basic usage of the VoiceProcessingManager.

    This script initializes the VoiceProcessingManager with default settings and runs it to process a voice command.
    The processed text is printed to the console. The script uses text-to-speech functionality without streaming.

    The script can be terminated early by a KeyboardInterrupt (Ctrl+C).
    """
    try:
        # Create a VoiceProcessingManager instance with default settings
        vpm = VoiceProcessingManager.create_default_instance()

        @vpm.action_manager.register_action
        def recording_flag():
            print("Recording flag is set")

        # Run the voice processing manager with text-to-speech but without streaming
        text = vpm.run(tts=True, streaming=False)
        print(f"Processed text: {text}")

    except KeyboardInterrupt:
        logging.info("Interrupted by user, shutting down.")


if __name__ == '__main__':
    main()
