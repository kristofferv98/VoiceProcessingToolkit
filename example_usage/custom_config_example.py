#!/usr/bin/env python3
"""
Example script demonstrating how to use the custom configuration system
with VoiceProcessingToolkit.
"""

import os
import sys
import logging
from termcolor import colored
from pathlib import Path

# Add the parent directory to the path to make imports work
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from VoiceProcessingToolkit.config import get_config, Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CustomConfigExample")

def print_step(message):
    """Print a step in the example process with color."""
    print(colored(f"\n> {message}", "cyan"))

def main():
    """Run the example using a custom configuration."""
    print_step("Starting Voice Processing with Custom Configuration Example")
    
    # Get the path to the example_config.json file
    config_path = os.path.join(parent_dir, "example_config.json")
    
    print_step(f"Loading configuration from {config_path}")
    
    # Check if the config file exists
    if not os.path.exists(config_path):
        print(colored(f"Error: Configuration file not found at {config_path}", "red"))
        print(colored("Please run this example from the repository root or create the example_config.json file.", "red"))
        return
    
    # Load the configuration
    custom_config = get_config(config_path)
    
    print_step("Configuration loaded successfully")
    print(f"Wake word: {custom_config.wake_word.wake_word}")
    print(f"Sensitivity: {custom_config.wake_word.sensitivity}")
    print(f"Output directory: {custom_config.paths.output_dir}")
    
    # Check if API keys are set
    if not custom_config.transcriber.api_key:
        print(colored("Warning: No ElevenLabs API key found in config or environment variables.", "yellow"))
        print(colored("Transcription will not work without an API key.", "yellow"))
    
    if not custom_config.wake_word.access_key:
        print(colored("Warning: No Porcupine access key found in config or environment variables.", "yellow"))
        print(colored("Wake word detection will not work without an access key.", "yellow"))
    
    # Create the VoiceProcessingManager with custom settings
    print_step("Creating VoiceProcessingManager with custom settings")
    manager = VoiceProcessingManager(
        wake_word=custom_config.wake_word.wake_word,
        sensitivity=custom_config.wake_word.sensitivity,
        output_dir=custom_config.paths.output_dir,
        access_key=custom_config.wake_word.access_key,
        transcriber_api_key=custom_config.transcriber.api_key
    )
    
    # Now we can use the manager to process voice commands
    print_step("Ready to process voice commands")
    print(colored("Say the wake word followed by your command.", "green"))
    print(colored(f"Wake word: {custom_config.wake_word.wake_word}", "green"))
    print(colored("Press Ctrl+C to exit", "yellow"))
    
    try:
        # Process a voice command (this will wait for the wake word, record, and transcribe)
        transcription = manager.run()
        
        if transcription:
            print_step("Transcription result")
            print(colored(f"Transcription: {transcription}", "green"))
        else:
            print_step("No valid transcription obtained")
            
    except KeyboardInterrupt:
        print_step("Exiting due to keyboard interrupt")
    finally:
        # Clean up resources
        manager.cleanup()
    
    print_step("Example completed")

if __name__ == "__main__":
    main() 