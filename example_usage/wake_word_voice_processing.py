#!/usr/bin/env python3
"""
Wake Word Voice Processing Example

This example demonstrates how to use VoiceProcessingToolkit with wake word detection.
It uses Cobra VAD (Voice Activity Detection) for improved speech recognition.

Features:
- Wake word activation ("computer" by default)
- Cobra VAD for superior voice detection
- Audio recording and transcription
- Proper resource management
"""

import os
import sys
import logging
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

def main():
    """
    Main function that demonstrates wake word detection.
    
    This function:
    1. Creates a configuration with wake word settings
    2. Initializes the voice processing manager
    3. Listens for the wake word before recording
    4. Transcribes the recorded audio
    5. Handles cleanup and exit
    """
    print(colored("Starting Wake Word Voice Processing Example", "green"))
    print(colored("========================================", "green"))
    
    # Create a configuration with wake word settings
    config = {
        "audio": {
            "use_cobra_vad": True,
            "voice_threshold": 0.8,
            "inactivity_limit": 2.0,
            "min_recording_length": 1.5,
            "buffer_length": 2.0
        },
        "wake_word": {
            "wake_word": "computer",  # You can change this to your preferred wake word
            "sensitivity": 0.7
        },
        "paths": {
            "output_dir": "recordings"
        }
    }
    
    # Create a VoiceProcessingManager with wake word detection enabled
    print(colored("Initializing VoiceProcessingManager with wake word detection...", "cyan"))
    manager = VoiceProcessingManager.create_with_config(
        config_path=None,
        use_wake_word=True,
        play_notification_sound=True
    )
    
    # Apply our custom configuration
    manager.config = Config.from_dict(config)
    
    try:
        print(colored(f"\nListening for wake word: '{config['wake_word']['wake_word']}'", "cyan"))
        print(colored("Say the wake word, then speak your command", "cyan"))
        print(colored("Press Ctrl+C to exit", "yellow"))
        
        # Run the voice processing pipeline
        result = manager.run(transcription=True)
        
        if result:
            print(colored(f"Transcription result: {result}", "green"))
        else:
            print(colored("No transcription result obtained", "yellow"))
        
    except KeyboardInterrupt:
        print(colored("\nExiting due to keyboard interrupt...", "yellow"))
    except Exception as e:
        print(colored(f"\nError: {str(e)}", "red"))
        if "access_key" in str(e).lower():
            print(colored("This is expected when using placeholder API keys.", "yellow"))
            print(colored("Set the PICOVOICE_APIKEY environment variable with a valid key.", "yellow"))
    finally:
        # Clean up resources
        manager.cleanup()
        print(colored("Resources cleaned up", "green"))

if __name__ == "__main__":
    main() 