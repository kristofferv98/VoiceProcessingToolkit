import logging
from VoiceProcessingToolkit.VoiceProcessingManager import VoiceProcessingManager
from VoiceProcessingToolkit.voice_detection.Voicerecorder import AudioRecorder
import threading

# Basic configuration
logging.basicConfig(level=logging.INFO)

save_audio_flag = threading.Event()


def main():
    """
    Demonstrates the basic usage of the VoiceProcessingManager.

    This script initializes the VoiceProcessingManager with default settings and runs it to process a voice command.
    The processed text is printed to the console. The script uses text-to-speech functionality without streaming.

    The script can be terminated early by a KeyboardInterrupt (Ctrl+C).
    """
    try:
        # Create a VoiceProcessingManager instance with default settings
        vpm = VoiceProcessingManager.create_default_instance()

        # Create an AudioRecorder instance
        audio_recorder = AudioRecorder()
        # Start the background recording thread
        background_recording_thread = threading.Thread(target=audio_recorder.perform_recording)
        background_recording_thread.start()

        @vpm.action_manager.register_action
        def recording_flag():
            # Set the flag to trigger saving the audio snapshot
            save_audio_flag.set()
            print("Recording flag is set")

        # Run the voice processing manager with text-to-speech but without streaming
        text = vpm.run(tts=True, streaming=False)
        print(f"Processed text: {text}")

    except KeyboardInterrupt:
        logging.info("Interrupted by user, shutting down.")
    finally:
        # Ensure the background recording thread is stopped
        if background_recording_thread.is_alive():
            audio_recorder.cleanup()
            background_recording_thread.join()


if __name__ == '__main__':
    main()
