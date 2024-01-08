import logging
import os
import signal
import sys
import threading
import pyaudio
import numpy as np
from dotenv import load_dotenv

from voice_detection.Combined_script import AudioDataProvider, CobraVAD, AudioRecorder
from wake_word_detector.ActionManager import ActionManager, register_action_decorator
from wake_word_detector.AudioStreamManager import AudioStream
from wake_word_detector.WakeWordDetector import WakeWordDetector

# [Include all the classes from your second script here]
# AudioDataProvider, CobraVAD, and AudioRecorder classes

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
picovoice_api_key = os.getenv('PICOVOICE_APIKEY')

# AudioStream parameters
rate = 16000
channels = 1
audio_format = pyaudio.paInt16
frames_per_buffer = 512

# Initialize the audio data provider
audio_data_provider = AudioDataProvider(format=audio_format, channels=channels, rate=rate,
                                        frames_per_buffer=frames_per_buffer)
audio_data_manager = AudioStream(rate, channels, audio_format, frames_per_buffer)
# Cobra VAD and Audio Recorder setup
frame_length = 1024
sample_rate = 16000
cobra_vad = CobraVAD(access_key=picovoice_api_key, frame_length=frame_length, sample_rate=sample_rate)
audio_recorder = AudioRecorder(cobra_vad, "output_directory_path")

# Create an instance of ActionManager and WakeWordDetector
action_manager = ActionManager()
wake_word_detector = WakeWordDetector(
    access_key=picovoice_api_key,
    wake_word='jarvis',
    sensitivity=0.5,
    action_manager=action_manager,
    audio_stream_manager=audio_data_manager,
    play_notification_sound=True
)

# Define a stop event for signaling the threads to stop
stop_event = threading.Event()


# Define an action to be executed when the wake word is detected
@register_action_decorator(action_manager)
def wake_word_action():
    logger.info("Wake word detected!")
    audio_data_provider.start_stream()
    audio_recorder.start_recording(audio_data_provider)


# Function to run the wake word detector
def run_wake_word_detector():
    while not stop_event.is_set():
        try:
            wake_word_detector.run()
        except Exception as e:
            logger.error(f"Wake Word Detector error: {e}")
            break


# Function to handle shutdown signal
def signal_handler(_signum, _frame):
    logger.info("Shutdown signal received")
    audio_recorder.stop_recording()
    audio_data_provider.stop_stream()
    stop_event.set()


# Register the signal handler for graceful shutdown
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Start the wake word detector in a separate thread
wake_word_thread = threading.Thread(target=run_wake_word_detector)
wake_word_thread.start()

# Wait for the thread to finish
wake_word_thread.join()
logger.info("Shutdown complete")
sys.exit(0)
