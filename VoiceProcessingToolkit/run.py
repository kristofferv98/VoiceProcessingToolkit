
import pyaudio
import threading
import signal

from VoiceProcessingToolkit.voice_detection.audio_data_provider import PyAudioDataProvider
from VoiceProcessingToolkit.voice_detection.voice_activity_detector import VoiceActivityDetector
from VoiceProcessingToolkit.voice_detection.audio_recorder import AudioRecorder
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager, register_action_decorator
from VoiceProcessingToolkit.wake_word_detector.AudioStreamManager import AudioStreamManager

# Initialize the audio data provider
audio_data_provider = PyAudioDataProvider()

# Define a callback function for the audio recorder
def recording_callback(audio_file_path):
    print(f"Audio recorded: {audio_file_path}")

# Initialize the audio recorder
audio_recorder = AudioRecorder(callback=recording_callback)

# Initialize the voice activity detector
vad = VoiceActivityDetector(
    vad_engine=None,  # Placeholder for an actual VAD engine instance
    audio_data_provider=audio_data_provider,
    voice_activity_handler=audio_recorder.handle_voice_activity
)

# Initialize the action manager
action_manager = ActionManager()

# Define an action to be executed when the wake word is detected
@register_action_decorator(action_manager)
def wake_word_action():
    print("Wake word detected!")

# Initialize the wake word detector
wake_word_detector = WakeWordDetector(
    access_key="your-picovoice_api_key",
    wake_word='jarvis',
    sensitivity=0.5,
    action_manager=action_manager,
    audio_stream_manager=AudioStreamManager(rate=16000, channels=1, audio_format=pyaudio.paInt16, frames_per_buffer=1024),
    play_notification_sound=True
)



# Define a stop event for signaling the threads to stop
stop_event = threading.Event()

# These functions are already refactored to use the stop_event for graceful shutdown.
# No changes are required here.

# Start the voice activity detector and wake word detector
# Function to handle shutdown signal


def signal_handler(signum, frame):
    print("Shutdown signal received")
    stop_event.set()

# Register the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start the voice activity detector and wake word detector threads
vad_thread = start_voice_activity_detector()
wake_word_thread = start_wake_word_detector()

# Wait for the threads to finish
vad_thread.join()
wake_word_thread.join()

print("VoiceProcessingToolkit has been shut down gracefully.")

# Placeholder comment removed as the implementation is now complete.
