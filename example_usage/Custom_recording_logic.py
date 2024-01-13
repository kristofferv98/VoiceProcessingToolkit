import logging

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager

# Basic configuration
logging.basicConfig(level=logging.INFO)


def main():
    """
    Demonstrates a custom usage of the VoiceProcessingManager.

    This script initializes the VoiceProcessingManager with custom recording settings and runs it without the wake word
    detector or text-to-speech functionality. This wil result in a recording with transcription that runs until the
    custom logic in the action manager is completed.

    The processed text is printed to the console.

    """

    # Create a VoiceProcessingManager instance with custom settings
    vpm = VoiceProcessingManager.create_default_instance(use_wake_word=False, voice_threshold=0.5, silence_limit=1,
                                                         min_recording_length=3, inactivity_limit=5)

    # Run the voice processing manager with text-to-speech but without streaming and without wake word detection
    text = vpm.run(tts=False)

    print(f"Processed text: {text}")


if __name__ == '__main__':
    main()
