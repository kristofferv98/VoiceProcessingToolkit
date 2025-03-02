# VoiceProcessingToolkit

Voice Processing Toolkit is a Python package for voice processing tasks, providing a comprehensive suite of tools for wake word detection, voice recording, and transcription.

## Introduction

This toolkit provides an end-to-end solution for voice processing applications, including wake word detection (using Porcupine), voice recording, and speech-to-text conversion (using ElevenLabs API). It features a modular design with well-defined interfaces, making it easy to extend or customize for your specific use case.

## Features

- Wake word detection using Picovoice Porcupine
- Voice activity detection using Picovoice Cobra VAD
- Advanced recording with configurable thresholds and timing parameters
- Audio transcription with multiple providers supported
- Modular design for easy extension and customization
- Comprehensive configuration system

## Major Changes in v2.0

- **Interface-based Architecture**: All components implement well-defined interfaces for better extensibility and testability.
- **Centralized Configuration**: Unified configuration system with dataclasses and JSON support.
- **Advanced Voice Detection**: Integration of Picovoice Cobra VAD for superior voice activity detection.
- **Improved Thread Management**: Better thread handling and resource management.
- **Enhanced Error Handling**: Comprehensive error handling with retry mechanisms.
- **Resource Management**: Proper cleanup of resources across all components.
- **Testing Framework**: Comprehensive unit and integration test suite.

## Installation

You can install the package using pip:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv add VoiceProcessingToolkit
```

## Usage

### Basic Usage

```python
from VoiceProcessingToolkit import VoiceProcessingManager

# Create a default manager instance
manager = VoiceProcessingManager.create_default_instance()

# Process a voice command (detects wake word, records voice, and transcribes)
transcription = manager.run()
print(f"Transcription: {transcription}")
```

### Custom Configuration

```python
from VoiceProcessingToolkit import VoiceProcessingManager, config

# Load custom configuration from file
custom_config = config.get_config("config.json")

# Create a manager with custom parameters
manager = VoiceProcessingManager(
    wake_word="jarvis",
    sensitivity=0.8,
    output_dir="my_recordings"
)

# Process a voice command
transcription = manager.run()
```

### Using Individual Components

```python
from VoiceProcessingToolkit.wake_word_detector import WakeWordDetector
from VoiceProcessingToolkit.voice_detection import AudioRecorder
from VoiceProcessingToolkit.transcription import ElevenLabsTranscriber

# Create components
wake_word_detector = WakeWordDetector(wake_word="alexa", sensitivity=0.7)
recorder = AudioRecorder(output_dir="recordings")
transcriber = ElevenLabsTranscriber()

# Use components independently
wake_word_detector.run_blocking()  # Wait for wake word
recording_path = recorder.perform_recording()  # Record voice
transcription = transcriber.transcribe_audio(recording_path)  # Transcribe
```

## Configuration

VoiceProcessingToolkit uses a flexible configuration system that supports environment variables, constructor parameters, and JSON configuration files.

### Environment Variables

- `PICOVOICE_APIKEY`: Your Picovoice API key for wake word detection and Cobra VAD
- `ELEVENLABS_API_KEY`: Your Eleven Labs API key for transcription

### JSON Configuration

You can provide a configuration file with the following structure:

```json
{
    "transcriber": {
        "provider": "elevenlabs",
        "model_id": "whisper-1",
        "max_retries": 3,
        "retry_delay": 2,
        "timeout": 30
    },
    "audio": {
        "rate": 16000,
        "channels": 1,
        "audio_format": "paInt16",
        "frames_per_buffer": 512,
        "energy_threshold": 300,
        "silence_threshold": 50,
        "min_speaking_time": 0.5,
        "min_silence_time": 0.5,
        "max_speaking_time": 10,
        "use_cobra_vad": true,
        "voice_threshold": 0.8,
        "silence_limit": 2.0,
        "inactivity_limit": 2.0,
        "min_recording_length": 2.0,
        "buffer_length": 2.0
    },
    "wake_word": {
        "wake_word": "computer",
        "sensitivity": 0.7,
        "access_key": "YOUR_PICOVOICE_ACCESS_KEY"
    },
    "paths": {
        "output_dir": "Wav_MP3",
        "notification_sound_dir": "notification_sounds"
    }
}
```

See `example_config.json` for a complete configuration example.

## Testing

The toolkit includes a comprehensive testing framework to ensure the reliability and functionality of all components. For more information, see [Testing](tests/README.md).

To run tests:

```bash
python -m pytest
```

To run tests with coverage:

```bash
python -m pytest --cov=VoiceProcessingToolkit
```

## Contributing

Contributions are welcome! Here are some ways you can contribute:

- Add support for additional transcription services
- Improve wake word detection accuracy
- Add new features
- Fix bugs
- Improve documentation

Please make sure to update tests as appropriate.

## Support

If you need help using this toolkit, please open an issue on the GitHub repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Development Status

This project is actively maintained and under development. The current version is 2.0.0.

## Acknowledgements

This toolkit uses the following open-source projects:

- [Porcupine](https://github.com/Picovoice/porcupine) for wake word detection
- [PyAudio](http://people.csail.mit.edu/hubert/pyaudio/) for audio input/output

## Contact Information

For questions, feedback, or support, please contact the maintainers through GitHub issues.

