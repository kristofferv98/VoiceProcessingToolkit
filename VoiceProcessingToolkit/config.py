import os
import json
import dataclasses
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union
import logging
import pathlib

logger = logging.getLogger(__name__)

@dataclass
class TranscriberConfig:
    """Configuration for transcription services."""
    provider: str = "elevenlabs"  # Available providers: elevenlabs, whisper
    api_key: Optional[str] = None  # Will be retrieved from environment variable if None
    model_id: str = "whisper-1"  # Default model for ElevenLabs
    max_retries: int = 3  # Maximum number of retries for failed API calls
    retry_delay: float = 2.0  # Delay between retries in seconds
    timeout: float = 30.0  # API call timeout in seconds


@dataclass
class AudioConfig:
    """Configuration for audio processing."""
    rate: int = 16000  # Audio sample rate
    channels: int = 1  # Number of audio channels (1 for mono, 2 for stereo)
    audio_format: int = 16  # Audio format (16 for 16-bit)
    frames_per_buffer: int = 1024  # Number of frames per buffer
    
    # Voice activity detection parameters
    energy_threshold: float = 300.0  # Energy level threshold for detecting speech
    silence_threshold: float = 50.0  # Energy level below which is considered silence
    min_speaking_time: float = 1.0  # Minimum duration of speech (seconds)
    min_silence_time: float = 1.5  # Minimum duration of silence to end recording (seconds)
    max_speaking_time: float = 30.0  # Maximum speaking time for a single recording (seconds)
    frame_duration_ms: float = 30.0  # Duration of each audio frame in milliseconds
    
    # Cobra VAD specific parameters
    voice_threshold: float = 0.8  # Threshold for Cobra VAD (0.0 to 1.0)
    inactivity_limit: float = 2.0  # Duration of inactivity before stopping recording (seconds)
    min_recording_length: float = 2.0  # Minimum recording length for a valid sample (seconds)
    buffer_length: float = 2.0  # Length of audio buffer in seconds (for context before speech)
    use_cobra_vad: bool = True  # Whether to use Cobra VAD instead of energy-based detection


@dataclass
class WakeWordConfig:
    """Configuration for wake word detection."""
    wake_word: str = "computer"  # Wake word to detect
    sensitivity: float = 0.75  # Sensitivity for wake word detection (0.0 to 1.0)
    access_key: Optional[str] = None  # Will be retrieved from environment variable if None
    notification_sound_path: Optional[str] = None  # Path to notification sound file


@dataclass
class PathConfig:
    """Configuration for file paths."""
    output_dir: str = os.path.join(os.getcwd(), "recordings")  # Directory for saving recordings
    notification_sound_dir: str = os.path.join(os.path.dirname(__file__), "wake_word_detector", "Wav_MP3")  # Directory for notification sounds
    
    def __post_init__(self):
        """Create any directories that don't exist."""
        os.makedirs(self.output_dir, exist_ok=True)


@dataclass
class Config:
    """Main configuration class."""
    transcriber: TranscriberConfig = dataclasses.field(default_factory=TranscriberConfig)
    audio: AudioConfig = dataclasses.field(default_factory=AudioConfig)
    wake_word: WakeWordConfig = dataclasses.field(default_factory=WakeWordConfig)
    paths: PathConfig = dataclasses.field(default_factory=PathConfig)
    
    def __post_init__(self):
        """Initialize with environment variables if applicable."""
        # Set API keys from environment variables if not set
        if self.transcriber.api_key is None:
            self.transcriber.api_key = os.getenv("ELEVEN_LABS_API_KEY")
        
        if self.wake_word.access_key is None:
            self.wake_word.access_key = os.getenv("PORCUPINE_ACCESS_KEY")
        
        # Set notification sound path if not set
        if self.wake_word.notification_sound_path is None:
            default_sound_path = os.path.join(self.paths.notification_sound_dir, "notification.wav")
            if os.path.exists(default_sound_path):
                self.wake_word.notification_sound_path = default_sound_path
            else:
                logger.warning(f"Default notification sound not found at {default_sound_path}")
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'Config':
        """
        Load configuration from a JSON file.
        
        Args:
            file_path: Path to the configuration file.
            
        Returns:
            Config: Loaded configuration.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_dict = json.load(f)
            
            # Convert nested dictionaries to dataclasses
            transcriber = TranscriberConfig(**config_dict.get("transcriber", {}))
            audio = AudioConfig(**config_dict.get("audio", {}))
            wake_word = WakeWordConfig(**config_dict.get("wake_word", {}))
            paths = PathConfig(**config_dict.get("paths", {}))
            
            return cls(
                transcriber=transcriber,
                audio=audio,
                wake_word=wake_word,
                paths=paths
            )
        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {e}")
            logger.info("Using default configuration")
            return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary.
        
        Returns:
            Dict[str, Any]: Configuration as a dictionary.
        """
        return {
            "transcriber": dataclasses.asdict(self.transcriber),
            "audio": dataclasses.asdict(self.audio),
            "wake_word": dataclasses.asdict(self.wake_word),
            "paths": dataclasses.asdict(self.paths)
        }
    
    def save_to_file(self, file_path: str) -> bool:
        """
        Save the configuration to a JSON file.
        
        Args:
            file_path: Path to save the configuration.
            
        Returns:
            bool: True if save was successful, False otherwise.
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=4)
            
            logger.info(f"Configuration saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration to {file_path}: {e}")
            return False


# Create a default configuration instance
default_config = Config()


def get_config(file_path: Optional[str] = None) -> Config:
    """
    Get the configuration, loading from a file if provided.
    
    Args:
        file_path: Path to a configuration file to load. If None, uses default config.
        
    Returns:
        Config: The configuration.
    """
    if file_path and os.path.exists(file_path):
        return Config.load_from_file(file_path)
    return default_config 