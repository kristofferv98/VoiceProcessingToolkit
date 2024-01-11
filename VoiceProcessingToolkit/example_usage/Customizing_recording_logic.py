import asyncio
import logging
import time

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager

# Basic configuration
logging.basicConfig(level=logging.INFO)


def main():
    """
    Demonstrates the basic usage of the VoiceProcessingManager.

    This script initializes the VoiceProcessingManager with custom recording settings and runs it to process a voice
    command. wake word is detected. Streaming is false, which may result in a more stable performance but will
    also increase the latency.

    The processed text is printed to the console. The script uses text-to-speech
    functionality without streaming.

    """

    # Create a VoiceProcessingManager instance with custom settings
    vpm = VoiceProcessingManager.create_default_instance(use_wake_word=False, voice_threshold=0.5, silence_limit=1,
                                                         min_recording_length=3, inactivity_limit=5)

    # Run the voice processing manager with text-to-speech but without streaming and without wake word detection
    text = vpm.run(tts=True, streaming=False)

    print(f"Processed text: {text}")


if __name__ == '__main__':
    main()
