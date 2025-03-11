import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class Config:
    """
    Simplified configuration class with flatter structure and sensible defaults.
    """
    
    def __init__(self, **kwargs):
        # Audio settings
        self.audio_rate = kwargs.get('audio_rate', 16000)
        self.audio_channels = kwargs.get('audio_channels', 1)
        self.audio_format = kwargs.get('audio_format', 16)  # 16-bit
        self.frames_per_buffer = kwargs.get('frames_per_buffer', 512)
        
        # Voice activity detection
        self.use_cobra_vad = kwargs.get('use_cobra_vad', True)
        self.voice_threshold = kwargs.get('voice_threshold', 0.8)
        self.energy_threshold = kwargs.get('energy_threshold', 300.0)
        self.silence_threshold = kwargs.get('silence_threshold', 50.0)
        self.min_speaking_time = kwargs.get('min_speaking_time', 1.0)
        self.min_silence_time = kwargs.get('min_silence_time', 1.5)
        self.max_speaking_time = kwargs.get('max_speaking_time', 30.0)
        self.frame_duration_ms = kwargs.get('frame_duration_ms', 30.0)
        self.inactivity_limit = kwargs.get('inactivity_limit', 2.0)
        self.min_recording_length = kwargs.get('min_recording_length', 2.0)
        self.buffer_length = kwargs.get('buffer_length', 2.0)
        
        # Wake word detection
        self.wake_word = kwargs.get('wake_word', 'computer')
        self.wake_word_sensitivity = kwargs.get('wake_word_sensitivity', 0.75)
        self.wake_word_access_key = kwargs.get('wake_word_access_key', os.getenv('PICOVOICE_APIKEY'))
        self.use_wake_word = kwargs.get('use_wake_word', True)
        self.play_notification_sound = kwargs.get('play_notification_sound', True)
        
        # Transcription
        self.transcriber_provider = kwargs.get('transcriber_provider', 'elevenlabs')
        self.transcriber_api_key = kwargs.get('transcriber_api_key', os.getenv('ELEVENLABS_API_KEY'))
        self.transcriber_model = kwargs.get('transcriber_model', 'whisper-1')
        self.transcriber_retries = kwargs.get('transcriber_retries', 3)
        self.transcriber_retry_delay = kwargs.get('transcriber_retry_delay', 2.0)
        self.transcriber_timeout = kwargs.get('transcriber_timeout', 30.0)
        
        # Paths
        self.output_dir = kwargs.get('output_dir', os.path.join(os.getcwd(), 'recordings'))
        self.notification_sound_dir = kwargs.get(
            'notification_sound_dir', 
            os.path.join(os.path.dirname(__file__), "wake_word_detector", "Wav_MP3")
        )
        
        # Create the output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set notification sound path
        self.notification_sound_path = kwargs.get('notification_sound_path', None)
        if self.notification_sound_path is None:
            default_sound_path = os.path.join(self.notification_sound_dir, "notification.wav")
            if os.path.exists(default_sound_path):
                self.notification_sound_path = default_sound_path
            else:
                logger.warning(f"Default notification sound not found at {default_sound_path}")
        
        # Wake word dataset recording
        self.save_wake_word_recordings = kwargs.get('save_wake_word_recordings', False)
        self.wake_word_output = kwargs.get('wake_word_output', os.path.join(self.output_dir, 'wake_word_dataset'))
        if self.save_wake_word_recordings:
            os.makedirs(self.wake_word_output, exist_ok=True)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """Create a Config instance from a dictionary."""
        # Flatten nested dictionaries (if present)
        flat_config = {}
        
        # Transcriber section
        if 'transcriber' in config_dict:
            for k, v in config_dict['transcriber'].items():
                flat_config[f'transcriber_{k}'] = v
                
        # Audio section
        if 'audio' in config_dict:
            for k, v in config_dict['audio'].items():
                if k == 'rate':
                    flat_config['audio_rate'] = v
                elif k == 'channels':
                    flat_config['audio_channels'] = v
                elif k == 'audio_format':
                    flat_config['audio_format'] = v
                else:
                    flat_config[k] = v
                
        # Wake word section
        if 'wake_word' in config_dict:
            for k, v in config_dict['wake_word'].items():
                if k == 'wake_word':
                    flat_config['wake_word'] = v
                elif k == 'sensitivity':
                    flat_config['wake_word_sensitivity'] = v
                else:
                    flat_config[f'wake_word_{k}'] = v
                
        # Paths section
        if 'paths' in config_dict:
            for k, v in config_dict['paths'].items():
                flat_config[k] = v
                
        # Add any top-level keys
        for k, v in config_dict.items():
            if not isinstance(v, dict):
                flat_config[k] = v
                
        return cls(**flat_config)
    
    @classmethod
    def from_file(cls, file_path: str) -> 'Config':
        """Load configuration from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            return cls.from_dict(config_dict)
        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {e}")
            logger.info("Using default configuration")
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def save_to_file(self, file_path: str) -> bool:
        """Save the configuration to a JSON file."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving configuration to {file_path}: {e}")
            return False

# Function to get configuration
def get_config(file_path: Optional[str] = None) -> Config:
    """Get configuration, loading from a file if provided."""
    if file_path and os.path.exists(file_path):
        return Config.from_file(file_path)
    return Config()

# Create a default configuration instance
default_config = Config() 