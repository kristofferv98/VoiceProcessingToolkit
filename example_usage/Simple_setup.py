#!/usr/bin/env python3
"""
Simple example demonstrating basic usage of the VoiceProcessingToolkit.

This script shows how to initialize and use the VoiceProcessingManager with default settings.
It demonstrates:
1. Basic initialization without wake word detection
2. Continuous voice processing
3. Proper signal handling for graceful shutdown
4. Use of the unified Config approach
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
from VoiceProcessingToolkit.config import Config, get_config
from dotenv import load_dotenv
import logging
import signal
from termcolor import colored

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Verify required API keys are set
required_keys = ['PICOVOICE_APIKEY', 'ELEVENLABS_API_KEY']
missing_keys = [key for key in required_keys if not os.getenv(key)]
if missing_keys:
    print(colored(f"Error: Missing required environment variables: {', '.join(missing_keys)}", "red"))
    print(colored("Please set these in your .env file", "yellow"))
    sys.exit(1)

def signal_handler(sig, frame):
    """Handle keyboard interrupts gracefully."""
    print(colored("\nExiting program due to keyboard interrupt.", "yellow"))
    sys.exit(0)

def main():
    """
    Initialize and run the VoiceProcessingManager with simplified configuration.
    
    This example:
    - Disables wake word detection for continuous recording
    - Disables notification sounds
    - Prints transcribed text to the console
    - Uses the new Config-based approach for simpler setup
    """
    print(colored("Initializing Voice Processing Manager...", "cyan"))
    
    # Create a VoiceProcessingManager instance using the new approach
    vpm = VoiceProcessingManager.create_with_config(
        config_path=None,  # Use default config
        wake_word='jarvis',
        use_wake_word=False,
        play_notification_sound=False
    )

    print(colored("Starting voice recording...", "green"))
    
    # Run the voice processing manager with transcription
    text = vpm.run(transcription=True)
    
    if text:
        print(colored(f"Transcribed text: {text}", "cyan"))
    else:
        print(colored("No transcription result obtained.", "yellow"))

if __name__ == '__main__':
    # Register signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print(colored("Running voice processing. Press Ctrl+C to exit.", "green"))
        print(colored("This example uses the new simplified config-based approach.", "cyan"))
        
        while True:
            main()
    except KeyboardInterrupt:
        print(colored("\nExiting program due to keyboard interrupt.", "yellow"))
        sys.exit(0)
