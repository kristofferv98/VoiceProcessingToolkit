import asyncio

import pyaudio

from VoiceProcessingToolkit.voice_detection.audio_data_provider import PyAudioDataProvider
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector
from VoiceProcessingToolkit.wake_word_detector.AudioStreamManager import AudioStreamManager
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager
from voice_detection.audio_recorder import AudioRecorder

# Define the sample rate, channels, and other audio parameters
SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
FRAMES_PER_BUFFER = 512

# Initialize the shared AudioStreamManager
audio_stream_manager = AudioStreamManager(SAMPLE_RATE, CHANNELS, FORMAT, FRAMES_PER_BUFFER)


# Initialize the Cobra VAD with a dummy voice activity handler
cobra_vad = PyAudioDataProvider(rate=SAMPLE_RATE, frames_per_buffer=FRAMES_PER_BUFFER)

# Initialize the ActionManager for the wake word detector with a dummy action
action_manager = ActionManager()
action_manager.register_action(lambda: print("Wake word detected!"))

# Initialize the WakeWordDetector with dummy parameters
wake_word_detector = WakeWordDetector(
    access_key='b2UbNJ2N5xNROBsICABolmKQwtQN7ARTRTSB+U0lZg+kDieYqcx7nw==',
    wake_word='jarvis',
    sensitivity=0.5,
    action_manager=action_manager,
    audio_stream_manager=audio_stream_manager,
    play_notification_sound=False
)

# Define a simple test routine
def test_routine():
    # Start the Cobra VAD process
    asyncio.run(AudioRecorder.start_recording(cobra_vad, lambda file_path: print(f"Recording saved to: {file_path}")))

    # Start the wake word detection in a separate thread
    wake_word_detector.run()

    # Ensure proper cleanup
    cobra_vad.cleanup()
    wake_word_detector.cleanup()

# Run the test routine
if __name__ == '__main__':
    test_routine()
