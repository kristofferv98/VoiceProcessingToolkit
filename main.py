import asyncio
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

# Initialize the Cobra VAD
# Note: You will need to provide the actual vad_engine and voice_activity_handler
cobra_vad = CobraVAD(vad_engine=None, audio_data_provider=audio_stream_manager, voice_activity_handler=None)

# Initialize the ActionManager for the wake word detector
action_manager = ActionManager()

# Define a simple action function that prints a message
def wake_word_action():
    print("Wake word detected!")

# Register the action with the ActionManager
action_manager.register_action(wake_word_action)

# Initialize the WakeWordDetector
# Note: You will need to provide the actual access_key and wake_word
wake_word_detector = WakeWordDetector(
    access_key='your-picovoice_api_key',
    wake_word='jarvis',
    sensitivity=0.5,
    action_manager=action_manager,
    audio_stream_manager=audio_stream_manager,
    play_notification_sound=True
)

# Start the Cobra VAD process
asyncio.run(cobra_vad.process_audio())

# Start the wake word detection in a separate thread
wake_word_detector.run()

# Ensure proper cleanup
cobra_vad.cleanup()
wake_word_detector.cleanup()
