import asyncio

import pyaudio

from VoiceProcessingToolkit.voice_detection.cobra import CobraVAD
from VoiceProcessingToolkit.voice_detection.audio_data_provider import PyAudioDataProvider
from VoiceProcessingToolkit.wake_word_detector.WakeWordDetector import WakeWordDetector
from VoiceProcessingToolkit.wake_word_detector.AudioStreamManager import AudioStreamManager
from VoiceProcessingToolkit.wake_word_detector.ActionManager import ActionManager

# Define the sample rate, channels, and other audio parameters
SAMPLE_RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
FRAMES_PER_BUFFER = 512

# Initialize the shared AudioStreamManager
audio_stream_manager = AudioStreamManager(SAMPLE_RATE, CHANNELS, FORMAT, FRAMES_PER_BUFFER)

# Initialize the Cobra VAD with a dummy voice activity handler function
def dummy_voice_activity_handler(voice_data: str) -> None:
    # This is where you would process the voice data
    pass

cobra_vad = CobraVAD(vad_engine=None, audio_data_provider=PyAudioDataProvider(), voice_activity_handler=dummy_voice_activity_handler)

# Initialize the ActionManager for the wake word detector with a dummy action
action_manager = ActionManager()
action_manager.register_action(lambda: print("Wake word detected!"))

# Initialize the WakeWordDetector with dummy parameters
wake_word_detector = WakeWordDetector(
    access_key='dummy_access_key',
    wake_word='dummy_wake_word',
    sensitivity=0.5,
    action_manager=action_manager,
    audio_stream_manager=audio_stream_manager,
    play_notification_sound=False
)

# Define a simple test routine
def test_test_routine():
    # Start the Cobra VAD process
    asyncio.run(cobra_vad.process_audio())

    # Start the wake word detection in a separate thread
    wake_word_detector.run()

    # Ensure proper cleanup
    cobra_vad.cleanup()
    wake_word_detector.cleanup()

# Run the test routine
if __name__ == '__main__':
    test_test_routine()
