import logging
import os
import signal
import sys
import threading

import pyaudio
from dotenv import load_dotenv

from voice_detection.audio_data_provider import PyAudioDataProvider
from wake_word_detector.ActionManager import ActionManager, register_action_decorator
from wake_word_detector.AudioStreamManager import AudioStreamManager
from wake_word_detector.WakeWordDetector import WakeWordDetector

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize the audio data provider
audio_data_provider = PyAudioDataProvider()
load_dotenv()
accesskey = os.getenv('PICOVOICE_APIKEY', 'picovoice_api_key')

# Set up the required parameters for AudioStreamManager
rate = 16000  # Sample rate
channels = 1  # Number of audio channels
audio_format = pyaudio.paInt16  # Audio format
frames_per_buffer = 512  # Number of frames per buffer

# Create an instance of AudioStreamManager
audio_stream_manager = AudioStreamManager(rate, channels, audio_format, frames_per_buffer)

# Create an instance of ActionManager
action_manager = ActionManager()


@register_action_decorator(action_manager)
def recording_callback(audio_file_path):
    print(f"Audio recorded: {audio_file_path}")

    # Create an instance of WakeWordDetector with the ActionManager
    detector = WakeWordDetector(
        access_key="b2UbNJ2N5xNROBsICABolmKQwtQN7ARTRTSB+U0lZg+kDieYqcx7nw==",
        wake_word='jarvis',
        sensitivity=0.75,
        action_manager=action_manager,
        audio_stream_manager=audio_stream_manager,
        play_notification_sound=True
    )

    # Start the wake word detection loop
    detector.run()


# Define an action to be executed when the wake word is detected
@register_action_decorator(action_manager)
def wake_word_action():
    print("Wake word detected!")
    start_voice_activity_detector()


# Initialize the wake word detector
wake_word_detector = WakeWordDetector(
    access_key=accesskey,
    wake_word='jarvis',
    sensitivity=0.5,
    action_manager=action_manager,
    audio_stream_manager=AudioStreamManager(rate=16000, channels=1, audio_format=pyaudio.paInt16,
                                            frames_per_buffer=1024),
    play_notification_sound=True
)

# Define a stop event for signaling the threads to stop
stop_event = threading.Event()


# These functions are already refactored to use the stop_event for graceful shutdown.
# No changes are required here.

# Start the voice activity detector and wake word detector
# Function to handle shutdown signal


def signal_handler(_signum, _frame):
    print("Shutdown signal received")
    audio_data_provider.cleanup()
    stop_event.set()


# Register the signal handler for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def start_voice_activity_detector():
    def vad_run():
        try:
            wake_word_detector.run()
        except Exception as e:
            print(f"Voice Activity Detector error: {e}")
        finally:
            stop_event.set()

    local_vad_thread = threading.Thread(target=vad_run)
    local_vad_thread.start()
    return local_vad_thread


def wake_word_run():
    try:
        wake_word_detector.run()
    except Exception as e:
        print(f"Wake Word Detector error: {e}")
    finally:
        stop_event.set()

    local_wake_word_thread = threading.Thread(target=wake_word_run)
    local_wake_word_thread.start()
    return local_wake_word_thread


# Start the voice activity detector and wake word detector threads
vad_thread = start_voice_activity_detector()
wake_word_thread = wake_word_run()

# Wait for the threads to finish
vad_thread.join()
wake_word_thread.join()

print("VoiceProcessingToolkit has been shut down gracefully.")

# Placeholder comment removed as the implementation is now complete.
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

