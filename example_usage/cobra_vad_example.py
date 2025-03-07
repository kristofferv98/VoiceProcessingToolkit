#!/usr/bin/env python3
"""
Example script demonstrating the use of Cobra VAD (Voice Activity Detection)
with the VoiceProcessingToolkit.

This script shows how to:
1. Configure and use Cobra VAD for superior voice detection
2. Set up custom configuration parameters
3. Handle wake word detection with Cobra VAD
4. Manage resources properly
"""

import os
import time
import logging
import sys
from pathlib import Path
from termcolor import colored

# Add the parent directory to the path if running directly
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Import the toolkit
from VoiceProcessingToolkit import VoiceProcessingManager
from VoiceProcessingToolkit.config import Config

def verify_environment():
    """
    Verify that all required environment variables are set.
    
    Returns:
        bool: True if all required variables are set, False otherwise
    """
    required_vars = ['PICOVOICE_APIKEY', 'ELEVENLABS_API_KEY']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(colored("ERROR: Missing required environment variables:", "red"))
        for var in missing_vars:
            print(colored(f"  - {var}", "yellow"))
        print("\nPlease set these variables in your environment or .env file")
        return False
    return True

def create_cobra_config():
    """
    Create a configuration dictionary for Cobra VAD.
    
    Returns:
        dict: Configuration dictionary with Cobra VAD settings
    """
    return {
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

def main():
    """
    Main function demonstrating Cobra VAD usage.
    
    This function:
    1. Verifies environment setup
    2. Creates custom configuration
    3. Initializes and runs the voice processing manager
    4. Handles cleanup and exit
    """
    # Verify environment variables
    if not verify_environment():
        return 1
    
    print(colored("Starting Cobra VAD Example", "green"))
    print(colored("============================", "green"))
    print("This example demonstrates using the Cobra VAD engine")
    print("for superior voice activity detection.")
    
    # Create configuration
    config = Config.from_dict(create_cobra_config())
    
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
    except Exception as e:
        print(colored(f"\nError: {str(e)}", "red"))
        return 1
    
    finally:
        # Clean up resources
        manager.cleanup()
        print(colored("Resources cleaned up", "green"))
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 