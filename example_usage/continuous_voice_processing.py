#!/usr/bin/env python3
"""
Continuous Voice Processing Example without Wake Word.

This example demonstrates how to use VoiceProcessingToolkit for continuous voice recording
and transcription without requiring a wake word to activate.

Features:
- Continuous voice activity detection
- Automatic audio recording when voice is detected
- Transcription of recorded audio
- Proper resource management and cleanup
"""

import sys
import os
from pathlib import Path
import signal
import logging
from termcolor import colored

# Add the parent directory to the path if running directly
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def signal_handler(sig, frame):
    """Handle keyboard interrupts gracefully."""
    print(colored("\nExiting program due to keyboard interrupt.", "yellow"))
    sys.exit(0)

def main():
    """
    Initialize and run the VoiceProcessingManager in continuous mode (no wake word).
    
    This function:
    1. Creates a VoiceProcessingManager with wake word detection disabled
    2. Listens continuously for voice activity
    3. Records and transcribes speech when detected
    4. Cleans up resources properly
    """
    print(colored("Initializing Voice Processing Manager...", "cyan"))
    
    # Create a VoiceProcessingManager instance with wake word detection disabled
    vpm = VoiceProcessingManager.create_with_config(
        config_path=None,  # Use default config
        use_wake_word=False,  # Disable wake word detection for continuous mode
        play_notification_sound=False
    )

    print(colored("Starting continuous voice recording...", "green"))
    print(colored("Any detected speech will be recorded and transcribed.", "cyan"))
    
    try:
        # Run the voice processing manager with transcription
        text = vpm.run(transcription=True)
        
        if text:
            print(colored(f"Transcribed text: {text}", "cyan"))
        else:
            print(colored("No transcription result obtained.", "yellow"))
    finally:
        # Ensure resources are properly cleaned up
        vpm.cleanup()

if __name__ == '__main__':
    # Register signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print(colored("Running continuous voice processing. Press Ctrl+C to exit.", "green"))
        
        while True:
            main()
    except KeyboardInterrupt:
        print(colored("\nExiting program due to keyboard interrupt.", "yellow"))
    except Exception as e:
        print(colored(f"\nError: {str(e)}", "red"))
    sys.exit(0)
