import logging
import asyncio
import time
from datetime import datetime

from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager

# Basic configuration
logging.basicConfig(level=logging.INFO)

def main():
    """
    Demonstrates the usage of the AudioRecorder with a rolling audio buffer.
    When the ActionManager decorator function is run, it saves a few seconds before and after in an audio file.
    The audio file is named by length and date.
    """
    try:
        # Create a VoiceProcessingManager instance with default settings
        vpm = VoiceProcessingManager.create_default_instance()

        # Create an AudioRecorder instance with a rolling buffer
        audio_recorder = AudioRecorder()

        @vpm.action_manager.register_action
        def save_audio_snapshot():
            # Calculate the timestamp for the filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Define the duration before and after the action to save
            pre_duration = 2  # seconds before the action
            post_duration = 2  # seconds after the action
            # Save the audio snapshot
            audio_recorder.save_audio_snapshot(pre_duration, post_duration, timestamp)

        # Run the voice processing manager with text-to-speech and streaming
        vpm.run(tts=True, streaming=True)

    except KeyboardInterrupt:
        logging.info("Interrupted by user, shutting down.")

if __name__ == '__main__':
    main()
