#!/usr/bin/env python3
"""
Example script demonstrating the use of Cobra VAD (Voice Activity Detection)
with the VoiceProcessingToolkit.

This script shows how to initialize and use the VoiceProcessingManager with
Cobra VAD enabled for superior voice detection.
"""

import os
import time
import logging
from termcolor import colored

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the toolkit
from VoiceProcessingToolkit import VoiceProcessingManager
from VoiceProcessingToolkit.config import Config

def main():
    # Ensure PICOVOICE_APIKEY is set
    if not os.environ.get('PICOVOICE_APIKEY'):
        print(colored("ERROR: PICOVOICE_APIKEY environment variable not set", "red"))
        print("Please set your Picovoice API key with:")
        print(colored("export PICOVOICE_APIKEY='your-api-key'", "yellow"))
        return 1
    
    print(colored("Starting Cobra VAD Example", "green"))
    print(colored("============================", "green"))
    print("This example demonstrates using the Cobra VAD engine")
    print("for superior voice activity detection.")
    
    # Create a custom configuration
    config_dict = {
        "audio": {
            "use_cobra_vad": True,
            "voice_threshold": 0.8,  # Higher threshold means less sensitive (0.0-1.0)
            "inactivity_limit": 2.0,  # Max time of inactivity before stopping (seconds)
            "min_recording_length": 1.5,  # Minimum recording length to be considered valid
            "buffer_length": 2.0  # Audio buffer length for context (seconds)
        },
        "wake_word": {
            "wake_word": "computer",  # Customize this to your preferred wake word
            "sensitivity": 0.7  # Wake word detection sensitivity (0.0-1.0)
        }
    }
    
    # Create config from dictionary
    config = Config.from_dict(config_dict)
    
    # Create a VoiceProcessingManager instance
    manager = VoiceProcessingManager.create_default_instance(
        access_key=os.environ.get('PICOVOICE_APIKEY'),
        output_directory="recordings",
        voice_threshold=config.audio.voice_threshold,
        inactivity_limit=config.audio.inactivity_limit,
        min_recording_length=config.audio.min_recording_length,
        buffer_length=config.audio.buffer_length
    )
    
    try:
        print(colored(f"\nListening for wake word: '{config.wake_word.wake_word}'", "cyan"))
        print(colored("Say something after the wake word is detected", "cyan"))
        print(colored("Press Ctrl+C to exit", "yellow"))
        
        # Run the manager in continuous mode
        manager.run_command(transcription=True)
        
    except KeyboardInterrupt:
        print(colored("\nExiting...", "yellow"))
    
    finally:
        # Clean up resources
        manager.cleanup()
        print(colored("Resources cleaned up", "green"))
    
    return 0

if __name__ == "__main__":
    exit(main()) 