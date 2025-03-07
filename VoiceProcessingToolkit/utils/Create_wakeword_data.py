#!/usr/bin/env python3
"""
Utility script for creating wake word datasets.

This script records audio snippets when the wake word is detected,
which can be used to create a custom dataset for wake word training.
"""

import logging
import os
import sys
import signal
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the path if running directly
parent_dir = str(Path(__file__).parent.parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager

# Configure logging
logging.basicConfig(level=logging.INFO)
load_dotenv()

# Set environment variables for API keys in .env file
os.getenv('PICOVOICE_APIKEY')
os.getenv('ELEVENLABS_API_KEY')

# Define signal handler
def signal_handler(sig, frame):
    print("\nExiting program due to keyboard interrupt.")
    sys.exit(0)

def main():
    """
    Demonstrates the basic usage of the WakeWordDetector to create a wake word dataset.

    This script initializes the VoiceProcessingManager with defined settings with the save_wake_word_recordings flag.
    This will create a folder called "wake_word_dataset" in the current working directory and save the wake word
    usage during usage. This can be used to create a wake word dataset for the wake word detector, based on normal
    usage as the usage of the wake word detector as it will not be affected by the recording of the wake word.
    The script can be terminated early by a KeyboardInterrupt (Ctrl+C).
    """

    # Create a WakeWordDetector instance with default settings
    wake_word_detector = VoiceProcessingManager.create_default_instance(use_wake_word=True, wake_word='computer',
                                                                        save_wake_word_recordings=True,
                                                                        play_notification_sound=False)

    # Run the wake word detector
    result = wake_word_detector.run(transcription=False)
    print("Wake word detection completed.")
    return result

if __name__ == '__main__':
    # Register signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("Running wake word dataset creation. Press Ctrl+C to exit.")
        main()
    except KeyboardInterrupt:
        print("\nExiting program due to keyboard interrupt.")
        sys.exit(0)
