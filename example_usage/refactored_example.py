#!/usr/bin/env python3
"""
Example demonstrating the refactored VoiceProcessingToolkit with improved resource management.

This example shows how to:
1. Use the simplified Config system
2. Take advantage of context managers for proper cleanup
3. Use the consolidated AudioManager
4. Work with the simplified interfaces
"""

import logging
import os
import sys
from pathlib import Path
from termcolor import colored

# Add the parent directory to the path if running directly
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import from the refactored toolkit
from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from VoiceProcessingToolkit.config import Config, get_config
from VoiceProcessingToolkit.audio.AudioManager import AudioManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RefactoredExample")

def print_step(message):
    """Print a step in the process with color."""
    print(colored(f"\n> {message}", "cyan"))

def verify_environment():
    """Check if required environment variables are set."""
    required_vars = ['PICOVOICE_APIKEY', 'ELEVENLABS_API_KEY']
    missing = [var for var in required_vars if not os.environ.get(var)]
    
    if missing:
        print(colored(f"Missing required environment variables: {', '.join(missing)}", "red"))
        print(colored("These are needed for wake word detection and transcription", "yellow"))
        return False
    return True

def main():
    """Run the example with the refactored toolkit."""
    print_step("Starting Refactored VoiceProcessingToolkit Example")
    
    if not verify_environment():
        return 1
    
    # Create a custom configuration
    print_step("Creating custom configuration")
    config = Config(
        # Audio settings
        audio_rate=16000,
        audio_channels=1,
        frames_per_buffer=512,
        
        # Voice activity detection
        use_cobra_vad=True,
        voice_threshold=0.8,
        inactivity_limit=2.0,
        min_recording_length=1.5,
        
        # Wake word detection
        wake_word="computer",
        wake_word_sensitivity=0.7,
        use_wake_word=True,
        play_notification_sound=True,
        
        # Output settings
        output_dir="recordings"
    )
    
    print(colored(f"Wake word: {config.wake_word}", "green"))
    print(colored(f"Sensitivity: {config.wake_word_sensitivity}", "green"))
    print(colored(f"Output directory: {config.output_dir}", "green"))
    
    # Using a context manager for proper resource cleanup
    print_step("Creating and using VoiceProcessingManager with context manager")
    try:
        with VoiceProcessingManager(config) as manager:
            print(colored("Say the wake word, followed by your voice command", "green"))
            print(colored("Manager will automatically clean up resources when done", "yellow"))
            
            # Run the voice processing pipeline
            result = manager.run(transcription=True)
            
            if result:
                print_step("Transcription Result")
                print(colored(f"Transcription: {result}", "green"))
            else:
                print_step("No transcription obtained")
    except KeyboardInterrupt:
        print_step("Interrupted by user")
    except Exception as e:
        print_step("Error occurred")
        print(colored(f"Error: {str(e)}", "red"))
    
    print_step("Example completed")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 