from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from dotenv import load_dotenv

import os
import logging
import sys
import signal

#logging.basicConfig(level=logging.INFO)
load_dotenv()

# Set environment variables for API keys in .env file
os.getenv('PICOVOICE_APIKEY')
os.getenv('OPENAI_API_KEY')
os.getenv('ELEVENLABS_API_KEY')

# Define signal handler
def signal_handler(sig, frame):
    print("\nExiting program due to keyboard interrupt.")
    sys.exit(0)

def main():
    """
    Demonstrates a custom usage of the VoiceProcessingManager.

    This script initializes the VoiceProcessingManager with custom recording settings and runs it without the wake word
    detector functionality. This will result in a recording with transcription that runs until the
    custom logic in the action manager is completed.

    The processed text is printed to the console.

    """

    # Create a VoiceProcessingManager instance with custom settings
    vpm = VoiceProcessingManager.create_default_instance(use_wake_word=True, wake_word='jarvis', voice_threshold=0.5, inactivity_limit=5,
                                                         min_recording_length=2)

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
        print("Running custom recording logic. Press Ctrl+C to exit.")
        main()
    except KeyboardInterrupt:
        print("\nExiting program due to keyboard interrupt.")
        sys.exit(0)
