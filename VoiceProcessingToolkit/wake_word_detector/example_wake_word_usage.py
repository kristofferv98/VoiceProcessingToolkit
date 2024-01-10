"""
Example usage of the WakeWordDetector to test wake word detection and save the audio snippet.
"""

import os
from wake_word_detector import WakeWordDetector, AudioStream, NotificationSoundManager, ActionManager

def main():
    # Set up the access key for Porcupine
    access_key = 'your-picovoice-api-key'  # Replace with your actual access key

    # Set up the audio stream parameters
    rate = 16000
    channels = 1
    audio_format = pyaudio.paInt16
    frames_per_buffer = 512

    # Set up the wake word parameters
    wake_word = 'jarvis'
    sensitivity = 0.5
    snippet_length = 3.0  # Length of the audio snippet in seconds

    # Set up the directory to save audio snippets
    save_audio_directory = 'saved_audio_snippets'
    if not os.path.exists(save_audio_directory):
        os.makedirs(save_audio_directory)

    # Initialize the audio stream manager
    audio_stream_manager = AudioStream(rate, channels, audio_format, frames_per_buffer)

    # Initialize the action manager
    action_manager = ActionManager()

    # Initialize the wake word detector
    detector = WakeWordDetector(
        access_key=access_key,
        wake_word=wake_word,
        sensitivity=sensitivity,
        action_manager=action_manager,
        audio_stream_manager=audio_stream_manager,
        play_notification_sound=True,
        save_audio_directory=save_audio_directory,
        snippet_length=snippet_length
    )

    # Run the wake word detector
    print("Listening for wake word...")
    detector.run_blocking()

if __name__ == '__main__':
    main()
