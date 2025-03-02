from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from dotenv import load_dotenv

import logging
import os
import sys
import signal

# logging.basicConfig(level=logging.INFO)
load_dotenv()

# Set environment variables for API keys in .env file
os.getenv('PICOVOICE_APIKEY')
os.getenv('ELEVENLABS_API_KEY')  # Used for speech-to-text

# Define signal handler
def signal_handler(sig, frame):
    print("\nExiting program due to keyboard interrupt.")
    sys.exit(0)

def main():
    """
    This example demonstrates the basic setup and usage of the VoiceProcessingManager.

    The script initializes the VoiceProcessingManager with default settings, and runs the manager to process voice
    commands. The processed text is printed to the console.
    """
    # Create a VoiceProcessingManager instance with default settings
    vpm = VoiceProcessingManager.create_default_instance(use_wake_word=False, play_notification_sound=False,
                                                         wake_word='jarvis')

    # Run the voice processing manager with transcription
    text = vpm.run(transcription=True)
    if text:
        print(f"Processed text: {text}")
    else:
        print("No transcription result obtained.")


if __name__ == '__main__':
    # Register signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("Running voice processing. Press Ctrl+C to exit.")
        while True:
            main()
    except KeyboardInterrupt:
        print("\nExiting program due to keyboard interrupt.")
        sys.exit(0)
