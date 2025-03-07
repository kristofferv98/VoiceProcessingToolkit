#!/usr/bin/env python3
"""
Simple example demonstrating basic usage of the VoiceProcessingToolkit.

This script shows how to initialize and use the VoiceProcessingManager with default settings.
It demonstrates:
1. Basic initialization without wake word detection
2. Continuous voice processing
3. Proper signal handling for graceful shutdown
"""

# Import sys and set up path properly if run directly
import sys
import os
from pathlib import Path

# Add the parent directory to the path if running directly
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from dotenv import load_dotenv
import logging
import signal

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Verify required API keys are set
required_keys = ['PICOVOICE_APIKEY', 'ELEVENLABS_API_KEY']
missing_keys = [key for key in required_keys if not os.getenv(key)]
if missing_keys:
    print(f"Error: Missing required environment variables: {', '.join(missing_keys)}")
    print("Please set these in your .env file")
    sys.exit(1)

def signal_handler(sig, frame):
    """Handle keyboard interrupts gracefully."""
    print("\nExiting program due to keyboard interrupt.")
    sys.exit(0)

def main():
    """
    Initialize and run the VoiceProcessingManager with default settings.
    
    This example:
    - Disables wake word detection for continuous recording
    - Disables notification sounds
    - Prints transcribed text to the console
    """
    # Create a VoiceProcessingManager instance with default settings
    vpm = VoiceProcessingManager.create_default_instance(
        use_wake_word=False,
        play_notification_sound=False,
        wake_word='jarvis'
    )

    # Run the voice processing manager with transcription
    text = vpm.run(transcription=True)
    if text:
        print(f"Transcribed text: {text}")
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
