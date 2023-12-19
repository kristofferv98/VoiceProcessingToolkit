from voice_detection.audio_data_provider import PyAudioDataProvider
from voice_detection.notification_sound_manager import NotificationSoundManager
from VOICEASSISTANT_V5.Agent_setup.Agents import handle_agent_message
from VOICEASSISTANT_V5.Voice_setup.Combined_audio_processing import combined_audio_processing
from VOICEASSISTANT_V5.config.global_config import config

class VoiceAssistant:
    def __init__(self):
        self.audio_data_provider = PyAudioDataProvider(...)
        self.notification_sound_manager = NotificationSoundManager(notification_path)
        # Initialize other necessary components here

    def typing_loop(self):
        # Implementation of typing loop

    def voice_loop(self):
        # Implementation of voice loop

    def run(self):
        # Implementation of the main application loop

    def cleanup(self):
        self.audio_data_provider.cleanup()
        # Clean up other resources here

# The rest of the code that initializes and runs the VoiceAssistant
